"""Code generation utilities for converting IR JSON into C# source.

The generator consumes the IR schema defined in ``ir_schema.py`` and renders
C# code via a Jinja2 template. The default template instantiates the proper
RobotLib robot implementation and emits one statement per IR command in the
sequence.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

from .ir_schema import ValidationResult, validate_ir_document

try:
    from jinja2 import Environment, FileSystemLoader, Template
except ImportError as exc:  # pragma: no cover - surfaced during runtime
    raise RuntimeError(
        "Jinja2 is required to run the code generator. Install it with 'pip install jinja2'."
    ) from exc

Number = (int, float)

TEMPLATE_DIRECTORY = Path(__file__).parent / "templates"
DEFAULT_TEMPLATE = "workflow.cs.j2"


class CodeGenerationError(RuntimeError):
    """Raised when the IR cannot be translated to C# code."""


ROBOT_FACTORY_MAP: Mapping[str, str] = {
    "fanuc": "new FanucRobot()",
    "kuka": "new KukaRobot()",
    "default": "new DefaultRobot()",
}


COMPARISON_OPERATORS: Mapping[str, str] = {
    "eq": "==",
    "neq": "!=",
    "lt": "<",
    "lte": "<=",
    "gt": ">",
    "gte": ">=",
}


LOGIC_OPERATORS: Mapping[str, str] = {
    "and": "&&",
    "or": "||",
}


ARITHMETIC_OPERATORS: Mapping[str, str] = {
    "add": "+",
    "minus": "-",
    "multiply": "*",
    "divide": "/",
}


MATH_SINGLE_FUNCTIONS: Mapping[str, str] = {
    "root": "Math.Sqrt",
    "abs": "Math.Abs",
    "ln": "Math.Log",
    "log10": "Math.Log10",
    "exp": "Math.Exp",
}


MATH_TRIG_FUNCTIONS: Mapping[str, str] = {
    "sin": "Math.Sin",
    "cos": "Math.Cos",
    "tan": "Math.Tan",
    "asin": "Math.Asin",
    "acos": "Math.Acos",
    "atan": "Math.Atan",
}


MATH_ROUND_FUNCTIONS: Mapping[str, str] = {
    "round": "Math.Round",
    "roundup": "Math.Ceiling",
    "rounddown": "Math.Floor",
}


MATH_CONSTANT_EXPRESSIONS: Mapping[str, str] = {
    "pi": "Math.PI",
    "e": "Math.E",
    "golden_ratio": "(1 + Math.Sqrt(5)) / 2",
    "sqrt2": "Math.Sqrt(2)",
    "sqrt1_2": "Math.Sqrt(0.5)",
    "infinity": "double.PositiveInfinity",
}


class CSharpEmitter:
    """Translate IR nodes into C# statements."""

    def __init__(self) -> None:
        self._lines: List[str] = []
        self._indent_level: int = 0
        self._unique_counter: int = 0
        self._use_collections: bool = False
        self._use_random: bool = False

    @property
    def lines(self) -> List[str]:
        return self._lines

    @property
    def use_collections(self) -> bool:
        return self._use_collections

    @property
    def use_random(self) -> bool:
        return self._use_random

    def emit_line(self, line: str = "") -> None:
        if line:
            indent = " " * (self._indent_level * 4)
            self._lines.append(f"{indent}{line}")
        else:
            self._lines.append("")

    def emit_comment(self, text: str) -> None:
        if not text:
            return
        for part in str(text).splitlines():
            self.emit_line(f"// {part}")

    def mark_store_usage(self) -> None:
        self._use_collections = True

    def emit_sequence(self, nodes: Iterable[Dict[str, Any]]) -> None:
        for node in nodes or []:
            self._emit_node(node)

    def _emit_node(self, node: Dict[str, Any]) -> None:
        if not isinstance(node, dict):
            raise CodeGenerationError("IR node must be an object.")

        node_type = node.get("node_type")
        if node_type == "command":
            self._emit_command_node(node)
        elif node_type == "if":
            self._emit_if_node(node)
        elif node_type == "repeat":
            self._emit_repeat_node(node)
        elif node_type == "while":
            self._emit_while_node(node)
        elif node_type == "for_range":
            self._emit_for_range_node(node)
        elif node_type == "for_each":
            raise CodeGenerationError("The 'for_each' node type is not supported for C# generation.")
        elif node_type == "flow":
            self._emit_flow_node(node)
        else:
            raise CodeGenerationError(f"Unsupported node_type '{node_type}'.")

    def _emit_command_node(self, node: Dict[str, Any]) -> None:
        name = node.get("command")
        params = node.get("parameters", {})
        comment = node.get("comment")
        if comment:
            self.emit_comment(comment)

        dispatcher = getattr(self, f"_command_{name}", None)
        if dispatcher is None:
            raise CodeGenerationError(f"Unsupported command '{name}'.")
        dispatcher(params, node)

    def _emit_if_node(self, node: Dict[str, Any]) -> None:
        branches = node.get("branches", [])
        for index, branch in enumerate(branches):
            keyword = "if" if index == 0 else "else if"
            condition_expr = self._expression(branch.get("condition"))
            self.emit_line(f"{keyword} ({condition_expr})")
            self.emit_line("{")
            with self._indentation():
                self.emit_sequence(branch.get("body", []))
            self.emit_line("}")

        else_branch = node.get("else_branch")
        if else_branch:
            self.emit_line("else")
            self.emit_line("{")
            with self._indentation():
                self.emit_sequence(else_branch)
            self.emit_line("}")

    def _emit_repeat_node(self, node: Dict[str, Any]) -> None:
        counter = self._unique_name("repeatIndex")
        limit_expr = self._expression(node.get("count"))
        loop_limit = f"Math.Max(0, (int)Math.Round({limit_expr}))"
        self.emit_line(f"for (var {counter} = 0; {counter} < {loop_limit}; {counter}++)")
        self.emit_line("{")
        with self._indentation():
            self.emit_sequence(node.get("body", []))
        self.emit_line("}")

    def _emit_while_node(self, node: Dict[str, Any]) -> None:
        condition = self._expression(node.get("condition"))
        mode = node.get("mode", "while")
        if mode == "until":
            condition = f"!({condition})"
        self.emit_line(f"while ({condition})")
        self.emit_line("{")
        with self._indentation():
            self.emit_sequence(node.get("body", []))
        self.emit_line("}")

    def _emit_for_range_node(self, node: Dict[str, Any]) -> None:
        variable_name = sanitize_identifier(str(node.get("variable", "i")))
        start_expr = self._expression(node.get("from"))
        end_expr = self._expression(node.get("to"))
        step_expr = self._expression(node.get("by"))

        start_name = self._unique_name(f"{variable_name}Start")
        end_name = self._unique_name(f"{variable_name}End")
        step_name = self._unique_name(f"{variable_name}Step")

        self.emit_line("{")
        with self._indentation():
            self.emit_line(f"var {start_name} = (int)Math.Round({start_expr});")
            self.emit_line(f"var {end_name} = (int)Math.Round({end_expr});")
            self.emit_line(f"var {step_name} = (int)Math.Round({step_expr});")
            self.emit_line(f"if ({step_name} == 0) {{ {step_name} = 1; }}")
            self.emit_line(
                f"for (var {variable_name} = {start_name}; "
                f"{step_name} > 0 ? {variable_name} <= {end_name} : {variable_name} >= {end_name}; "
                f"{variable_name} += {step_name})"
            )
            self.emit_line("{")
            with self._indentation():
                self.emit_sequence(node.get("body", []))
            self.emit_line("}")
        self.emit_line("}")

    def _emit_flow_node(self, node: Dict[str, Any]) -> None:
        flow = node.get("flow")
        if flow == "break":
            self.emit_line("break;")
        elif flow == "continue":
            self.emit_line("continue;")
        else:
            raise CodeGenerationError(f"Unsupported flow directive '{flow}'.")

    def _unique_name(self, stem: str) -> str:
        self._unique_counter += 1
        return f"{stem}_{self._unique_counter}"

    @contextmanager
    def _indentation(self):
        self._indent_level += 1
        try:
            yield
        finally:
            self._indent_level -= 1

    def _expression(self, expr: Any) -> str:
        if not isinstance(expr, dict):
            raise CodeGenerationError("Expression node must be an object.")

        expr_type = expr.get("expr_type")
        if not isinstance(expr_type, str):
            raise CodeGenerationError("Expression missing 'expr_type'.")

        if expr_type == "literal_number":
            value = expr.get("value")
            if not isinstance(value, Number) or isinstance(value, bool):
                raise CodeGenerationError("Numeric literal requires a number value.")
            return format_number(value)

        if expr_type == "literal_boolean":
            value = expr.get("value")
            if not isinstance(value, bool):
                raise CodeGenerationError("Boolean literal requires a boolean value.")
            return format_bool(value)

        if expr_type == "literal_null":
            return "null"

        if expr_type == "comparison":
            op = expr.get("op")
            operator = COMPARISON_OPERATORS.get(op)
            if operator is None:
                raise CodeGenerationError(f"Unsupported comparison operator '{op}'.")
            left = self._expression(expr.get("left"))
            right = self._expression(expr.get("right"))
            return f"({left}) {operator} ({right})"

        if expr_type == "logic_binary":
            op = expr.get("op")
            operator = LOGIC_OPERATORS.get(op)
            if operator is None:
                raise CodeGenerationError(f"Unsupported logic operator '{op}'.")
            left = self._expression(expr.get("left"))
            right = self._expression(expr.get("right"))
            return f"({left}) {operator} ({right})"

        if expr_type == "logic_not":
            argument = self._expression(expr.get("argument"))
            return f"!({argument})"

        if expr_type == "ternary":
            condition = self._expression(expr.get("condition"))
            when_true = self._expression(expr.get("when_true"))
            when_false = self._expression(expr.get("when_false"))
            return f"({condition}) ? ({when_true}) : ({when_false})"

        if expr_type == "arithmetic":
            op = expr.get("op")
            left = self._expression(expr.get("left"))
            right = self._expression(expr.get("right"))
            if op == "power":
                return f"Math.Pow({left}, {right})"
            operator = ARITHMETIC_OPERATORS.get(op)
            if operator is None:
                raise CodeGenerationError(f"Unsupported arithmetic operator '{op}'.")
            return f"({left}) {operator} ({right})"

        if expr_type == "math_single":
            op = expr.get("op")
            argument = self._expression(expr.get("argument"))
            if op == "neg":
                return f"-({argument})"
            if op == "pow10":
                return f"Math.Pow(10, {argument})"
            function_name = MATH_SINGLE_FUNCTIONS.get(op)
            if function_name is None:
                raise CodeGenerationError(f"Unsupported math single operator '{op}'.")
            return f"{function_name}({argument})"

        if expr_type == "math_trig":
            op = expr.get("op")
            function_name = MATH_TRIG_FUNCTIONS.get(op)
            if function_name is None:
                raise CodeGenerationError(f"Unsupported trigonometric operator '{op}'.")
            argument = self._expression(expr.get("argument"))
            if op in {"sin", "cos", "tan"}:
                argument = self._degrees_to_radians(argument)
                return f"{function_name}({argument})"
            # Inverse trig functions return degrees
            return self._radians_to_degrees(f"{function_name}({argument})")

        if expr_type == "math_constant":
            constant = expr.get("constant")
            value = MATH_CONSTANT_EXPRESSIONS.get(constant)
            if value is None:
                raise CodeGenerationError(f"Unsupported math constant '{constant}'.")
            return value

        if expr_type == "math_round":
            op = expr.get("op")
            argument = self._expression(expr.get("argument"))
            function_name = MATH_ROUND_FUNCTIONS.get(op)
            if function_name is None:
                raise CodeGenerationError(f"Unsupported math round operator '{op}'.")
            return f"{function_name}({argument})"

        if expr_type == "math_modulo":
            left = self._expression(expr.get("left"))
            right = self._expression(expr.get("right"))
            return f"({left}) % ({right})"

        if expr_type == "math_constrain":
            value_expr = self._expression(expr.get("value"))
            low_expr = self._expression(expr.get("low"))
            high_expr = self._expression(expr.get("high"))
            return f"Math.Min(Math.Max({value_expr}, {low_expr}), {high_expr})"

        if expr_type == "math_random_int":
            low_expr = self._expression(expr.get("low"))
            high_expr = self._expression(expr.get("high"))
            self._require_random()
            return (
                "random.Next((int)Math.Round(Math.Min({low}, {high})), "
                "(int)Math.Round(Math.Max({low}, {high})) + 1)"
            ).format(low=low_expr, high=high_expr)

        if expr_type == "math_random_float":
            self._require_random()
            return "random.NextDouble()"

        raise CodeGenerationError(f"Unsupported expression type '{expr_type}'.")

    def _degrees_to_radians(self, argument: str) -> str:
        return f"({argument}) * Math.PI / 180.0"

    def _radians_to_degrees(self, argument: str) -> str:
        return f"({argument}) * 180.0 / Math.PI"

    def _require_random(self) -> None:
        self._use_random = True

    # --- Command handlers -------------------------------------------------
    def _command_connect_robot(self, params: Dict[str, Any], entry: Dict[str, Any]) -> None:
        ip = _expect_string(params, "ip_address")
        port = _expect_number(params, "port")
        timeout = params.get("timeout_ms")
        if timeout is not None:
            self.emit_comment(f"timeout_ms: {timeout}")
        self.emit_line(f"robot.ConnectRobot({_format_string(ip)}, {format_number(port)});")

    def _command_disconnect_robot(self, params: Dict[str, Any], entry: Dict[str, Any]) -> None:
        self.emit_line("robot.DisconnectRobot();")

    def _command_power_on_servo(self, params: Dict[str, Any], entry: Dict[str, Any]) -> None:
        self.emit_line("robot.PowerOnServo();")

    def _command_power_off_servo(self, params: Dict[str, Any], entry: Dict[str, Any]) -> None:
        self.emit_line("robot.PowerOffServo();")

    def _command_set_speed(self, params: Dict[str, Any], entry: Dict[str, Any]) -> None:
        percentage = _expect_number(params, "percentage")
        self.emit_line(f"robot.SetSpeed({format_number(percentage)});")

    def _command_set_acceleration(self, params: Dict[str, Any], entry: Dict[str, Any]) -> None:
        percentage = _expect_number(params, "percentage")
        self.emit_line(f"robot.SetAcceleration({format_number(percentage)});")

    def _command_move_to(self, params: Dict[str, Any], entry: Dict[str, Any]) -> None:
        x = _expect_number(params, "x")
        y = _expect_number(params, "y")
        z = _expect_number(params, "z")
        speed = params.get("speed_percentage")
        if speed is not None:
            self.emit_comment(f"speed_percentage override: {speed}")
        self.emit_line(
            "robot.MoveTo({x}, {y}, {z});".format(
                x=format_number(x), y=format_number(y), z=format_number(z)
            )
        )

    def _command_move_joint(self, params: Dict[str, Any], entry: Dict[str, Any]) -> None:
        joints = [format_number(_expect_number(params, f"j{i}")) for i in range(1, 7)]
        speed = params.get("speed_percentage")
        if speed is not None:
            self.emit_comment(f"speed_percentage override: {speed}")
        joined = ", ".join(joints)
        self.emit_line(f"robot.MoveJoint({joined});")

    def _command_move_linear(self, params: Dict[str, Any], entry: Dict[str, Any]) -> None:
        coords = [
            format_number(_expect_number(params, axis))
            for axis in ("x", "y", "z", "rx", "ry", "rz")
        ]
        speed = params.get("speed_percentage")
        if speed is not None:
            self.emit_comment(f"speed_percentage override: {speed}")
        self.emit_line(f"robot.MoveLinear({', '.join(coords)});")

    def _command_move_circular(self, params: Dict[str, Any], entry: Dict[str, Any]) -> None:
        via = _expect_cartesian(params, "via_point")
        end = _expect_cartesian(params, "end_point")
        via_expr = format_cartesian(via)
        end_expr = format_cartesian(end)
        self.emit_line(f"robot.MoveCircular({via_expr}, {end_expr});")

    def _command_stop_motion(self, params: Dict[str, Any], entry: Dict[str, Any]) -> None:
        stop_type = params.get("stop_type")
        if stop_type is not None:
            self.emit_comment(f"stop_type: {stop_type}")
        self.emit_line("robot.StopMotion();")

    def _command_wait_for_move_finish(self, params: Dict[str, Any], entry: Dict[str, Any]) -> None:
        timeout = params.get("timeout_ms")
        if timeout is not None:
            self.emit_comment(f"timeout_ms: {timeout}")
        self.emit_line("robot.WaitForMoveFinish();")

    def _command_get_current_joint_position(
        self, params: Dict[str, Any], entry: Dict[str, Any]
    ) -> None:
        store_as = params.get("store_as")
        if store_as:
            identifier = sanitize_identifier(store_as)
            assignment = f"var {identifier} = robot.GetCurrentJointPosition();"
            self.emit_line(assignment)
            self.emit_line(_store_variable(identifier, store_as))
            self.mark_store_usage()
        else:
            self.emit_line("robot.GetCurrentJointPosition();")

    def _command_get_current_cartesian_position(
        self, params: Dict[str, Any], entry: Dict[str, Any]
    ) -> None:
        store_as = params.get("store_as")
        if store_as:
            identifier = sanitize_identifier(store_as)
            assignment = f"var {identifier} = robot.GetCurrentCartesianPosition();"
            self.emit_line(assignment)
            self.emit_line(_store_variable(identifier, store_as))
            self.mark_store_usage()
        else:
            self.emit_line("robot.GetCurrentCartesianPosition();")

    def _command_get_robot_status(self, params: Dict[str, Any], entry: Dict[str, Any]) -> None:
        store_as = params.get("store_as")
        if store_as:
            identifier = sanitize_identifier(store_as)
            assignment = f"var {identifier} = robot.GetRobotStatus();"
            self.emit_line(assignment)
            self.emit_line(_store_variable(identifier, store_as))
            self.mark_store_usage()
        else:
            self.emit_line("robot.GetRobotStatus();")

    def _command_set_digital_output(self, params: Dict[str, Any], entry: Dict[str, Any]) -> None:
        port = _expect_number(params, "port")
        value = _expect_bool(params, "value")
        self.emit_line(
            f"robot.SetDigitalOutput({format_number(port)}, {format_bool(value)});"
        )

    def _command_get_digital_input(self, params: Dict[str, Any], entry: Dict[str, Any]) -> None:
        port = _expect_number(params, "port")
        store_as = params.get("store_as")
        call = f"robot.GetDigitalInput({format_number(port)})"
        if store_as:
            identifier = sanitize_identifier(store_as)
            self.emit_line(f"var {identifier} = {call};")
            self.emit_line(_store_variable(identifier, store_as))
            self.mark_store_usage()
        else:
            self.emit_line(f"{call};")

    def _command_set_tool_coordinate(self, params: Dict[str, Any], entry: Dict[str, Any]) -> None:
        tool_data = _expect_list(params, "tool_data", length=6, item_type="number")
        values = ", ".join(format_number(v) for v in tool_data)
        self.emit_line(f"robot.SetToolCoordinate(new double[] {{ {values} }});")

    def _command_set_user_coordinate(self, params: Dict[str, Any], entry: Dict[str, Any]) -> None:
        user_data = _expect_list(params, "user_data", length=6, item_type="number")
        values = ", ".join(format_number(v) for v in user_data)
        self.emit_line(f"robot.SetUserCoordinate(new double[] {{ {values} }});")

    def _command_grab(self, params: Dict[str, Any], entry: Dict[str, Any]) -> None:
        self.emit_line("robot.Grab();")

    def _command_release(self, params: Dict[str, Any], entry: Dict[str, Any]) -> None:
        self.emit_line("robot.Release();")

    def _command_print_numbers(self, params: Dict[str, Any], entry: Dict[str, Any]) -> None:
        self.emit_line("robot.PrintNumbers();")


# --- Helper functions ------------------------------------------------------

def generate_csharp_source(
    ir_document: Dict[str, Any],
    *,
    template_path: str | Path | None = None,
) -> str:
    """Render the provided IR document to C# source text."""

    validation: ValidationResult = validate_ir_document(ir_document)
    validation.raise_for_errors()

    metadata = ir_document.get("metadata", {}) or {}
    brand = str(metadata.get("robot_brand", "default")).lower()
    robot_factory = metadata.get("robot_factory") or ROBOT_FACTORY_MAP.get(brand, "new DefaultRobot()")

    namespace = metadata.get("namespace", "GeneratedWorkflows")
    class_name = metadata.get("class_name", "RobotProgram")
    method_name = metadata.get("method_name", "Run")

    attach_console_logger = bool(metadata.get("attach_console_logger", True))

    emitter = CSharpEmitter()
    emitter.emit_sequence(ir_document.get("sequence", []))

    env = _create_environment(template_path)
    template: Template = env.get_template(DEFAULT_TEMPLATE)
    return template.render(
        namespace=namespace,
        class_name=class_name,
        method_name=method_name,
        robot_factory=robot_factory,
        attach_console_logger=attach_console_logger,
        use_collections=emitter.use_collections,
        use_random=emitter.use_random,
        body_lines=emitter.lines,
    )


def generate_from_file(ir_path: str | Path, *, output_path: str | Path | None = None) -> str:
    """Load an IR JSON file and return or write the generated C# source."""

    with open(ir_path, "r", encoding="utf-8") as handle:
        document = json.load(handle)

    source = generate_csharp_source(document)

    if output_path is not None:
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(source)
        return str(output_path)
    return source


def _store_variable(identifier: str, key: str) -> str:
    literal_key = _format_string_literal(key)
    return f"variables[{literal_key}] = {identifier};"


def _expect_string(data: Dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise CodeGenerationError(f"Field '{key}' must be a string.")
    return value


def _expect_number(data: Dict[str, Any], key: str) -> float:
    value = data.get(key)
    if not isinstance(value, Number) or isinstance(value, bool):
        raise CodeGenerationError(f"Field '{key}' must be a number.")
    return float(value)


def _expect_bool(data: Dict[str, Any], key: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise CodeGenerationError(f"Field '{key}' must be a boolean.")
    return value


def _expect_list(
    data: Dict[str, Any],
    key: str,
    *,
    length: int | None = None,
    item_type: str | None = None,
) -> List[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise CodeGenerationError(f"Field '{key}' must be a list.")
    if length is not None and len(value) != length:
        raise CodeGenerationError(f"Field '{key}' must contain exactly {length} items.")
    if item_type == "number":
        for index, element in enumerate(value):
            if not isinstance(element, Number) or isinstance(element, bool):
                raise CodeGenerationError(
                    f"Field '{key}[{index}]' must be a number."
                )
    return value


def _expect_cartesian(data: Dict[str, Any], key: str) -> Dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise CodeGenerationError(f"Field '{key}' must be a Cartesian object.")
    for axis in ("x", "y", "z", "rx", "ry", "rz"):
        component = value.get(axis)
        if not isinstance(component, Number) or isinstance(component, bool):
            raise CodeGenerationError(f"Field '{key}.{axis}' must be a number.")
    return value


def _format_string_literal(value: str) -> str:
    return json.dumps(value)


def _format_string(value: str) -> str:
    return json.dumps(value)


def format_number(value: float) -> str:
    if math.isfinite(value):
        if float(value).is_integer():
            return str(int(value))
        formatted = ("{0:.6f}".format(value)).rstrip("0").rstrip(".")
        return formatted
    if math.isnan(value):
        return "double.NaN"
    if value > 0:
        return "double.PositiveInfinity"
    return "double.NegativeInfinity"


def format_bool(value: bool) -> str:
    return "true" if value else "false"


def format_cartesian(data: Mapping[str, Any]) -> str:
    parts = [
        f"{axis.upper()} = {format_number(float(data[axis]))}"
        for axis in ("x", "y", "z", "rx", "ry", "rz")
    ]
    return "new CartesianPoint { " + ", ".join(parts) + " }"


def sanitize_identifier(name: str) -> str:
    sanitized = "".join(ch if ch.isalnum() else "_" for ch in name)
    if not sanitized:
        sanitized = "value"
    if sanitized[0].isdigit():
        sanitized = "_" + sanitized
    return sanitized


def _create_environment(custom_template_path: str | Path | None) -> Environment:
    if custom_template_path is not None:
        template_dir = Path(custom_template_path).resolve()
        loader = FileSystemLoader(str(template_dir))
    else:
        loader = FileSystemLoader(str(TEMPLATE_DIRECTORY))
    return Environment(loader=loader, autoescape=False, trim_blocks=True, lstrip_blocks=True)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate C# code from robot IR JSON.")
    parser.add_argument("ir_path", help="Path to the IR JSON file.")
    parser.add_argument(
        "-o",
        "--output",
        help="Optional path to write the generated C# source. Default prints to stdout.",
    )
    parser.add_argument(
        "-t",
        "--template-dir",
        help="Optional custom template directory overriding the bundled templates.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        with open(args.ir_path, "r", encoding="utf-8") as handle:
            document = json.load(handle)
        source = generate_csharp_source(document, template_path=args.template_dir)
    except FileNotFoundError as exc:
        parser.error(str(exc))
    except json.JSONDecodeError as exc:
        parser.error(f"Failed to parse JSON: {exc}")
    except (CodeGenerationError, RuntimeError) as exc:
        parser.error(str(exc))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(source)
    else:
        sys.stdout.write(source)
    return 0


__all__ = [
    "generate_csharp_source",
    "generate_from_file",
    "CodeGenerationError",
]


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
