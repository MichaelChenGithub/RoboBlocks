"""Intermediate Representation (IR) schema and validation utilities.

The IR is designed as a JSON document that maps directly to the robot
capabilities defined in ``RobotLib.BaseRobot``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

IR_VERSION = "1.0"

Number = (int, float)


@dataclass
class ValidationResult:
    """Represents the outcome of validating an IR document."""

    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def raise_for_errors(self) -> None:
        """Raise ``ValueError`` if any validation errors are present."""
        if not self.valid:
            raise ValueError("\n".join(self.errors))


@dataclass(frozen=True)
class ParameterSpec:
    """Specification for a single command parameter."""

    name: str
    value_type: str
    required: bool = True
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    length: Optional[int] = None
    item_type: Optional[str] = None
    description: str = ""


@dataclass(frozen=True)
class CommandSpec:
    """Specification describing a robot command entry."""

    name: str
    description: str
    parameters: Tuple[ParameterSpec, ...] = tuple()
    optional_parameters: Tuple[ParameterSpec, ...] = tuple()


CARTESIAN_FIELDS = ("x", "y", "z", "rx", "ry", "rz")


def _cartesian_param(name: str, *, required: bool = True) -> ParameterSpec:
    return ParameterSpec(
        name=name,
        value_type="cartesian_point",
        required=required,
        description="Position and orientation tuple (x,y,z,rx,ry,rz).",
    )


def _percentage_param(name: str) -> ParameterSpec:
    return ParameterSpec(
        name=name,
        value_type="number",
        min_value=0,
        max_value=100,
        description="Percentage value between 0 and 100.",
    )


COMMAND_SPECS: Dict[str, CommandSpec] = {
    "connect_robot": CommandSpec(
        name="connect_robot",
        description="Open a connection to the robot controller.",
        parameters=(
            ParameterSpec("ip_address", "string", description="Target robot IP address."),
            ParameterSpec("port", "number", description="Target robot port."),
        ),
        optional_parameters=(
            ParameterSpec(
                "timeout_ms",
                "number",
                required=False,
                min_value=0,
                description="Optional connection timeout in milliseconds.",
            ),
        ),
    ),
    "disconnect_robot": CommandSpec(
        name="disconnect_robot",
        description="Close the robot connection.",
    ),
    "power_on_servo": CommandSpec(
        name="power_on_servo",
        description="Enable robot motors/servo power.",
    ),
    "power_off_servo": CommandSpec(
        name="power_off_servo",
        description="Disable robot motors/servo power.",
    ),
    "set_speed": CommandSpec(
        name="set_speed",
        description="Set the base motion speed percentage.",
        parameters=(_percentage_param("percentage"),),
    ),
    "set_acceleration": CommandSpec(
        name="set_acceleration",
        description="Set the base motion acceleration percentage.",
        parameters=(_percentage_param("percentage"),),
    ),
    "move_to": CommandSpec(
        name="move_to",
        description="Move to a simple XYZ position.",
        parameters=(
            ParameterSpec("x", "number"),
            ParameterSpec("y", "number"),
            ParameterSpec("z", "number"),
        ),
        optional_parameters=(
            ParameterSpec(
                "speed_percentage",
                "number",
                required=False,
                min_value=0,
                max_value=100,
                description="Override speed just for this motion.",
            ),
        ),
    ),
    "move_joint": CommandSpec(
        name="move_joint",
        description="Move robot using joint angles.",
        parameters=(
            ParameterSpec("j1", "number"),
            ParameterSpec("j2", "number"),
            ParameterSpec("j3", "number"),
            ParameterSpec("j4", "number"),
            ParameterSpec("j5", "number"),
            ParameterSpec("j6", "number"),
        ),
        optional_parameters=(
            ParameterSpec(
                "speed_percentage",
                "number",
                required=False,
                min_value=0,
                max_value=100,
                description="Override speed just for this motion.",
            ),
        ),
    ),
    "move_linear": CommandSpec(
        name="move_linear",
        description="Linear move in Cartesian space.",
        parameters=(
            ParameterSpec("x", "number"),
            ParameterSpec("y", "number"),
            ParameterSpec("z", "number"),
            ParameterSpec("rx", "number"),
            ParameterSpec("ry", "number"),
            ParameterSpec("rz", "number"),
        ),
        optional_parameters=(
            ParameterSpec(
                "speed_percentage",
                "number",
                required=False,
                min_value=0,
                max_value=100,
                description="Override speed just for this motion.",
            ),
        ),
    ),
    "move_circular": CommandSpec(
        name="move_circular",
        description="Circular arc through via-point to end-point.",
        parameters=(
            _cartesian_param("via_point"),
            _cartesian_param("end_point"),
        ),
    ),
    "stop_motion": CommandSpec(
        name="stop_motion",
        description="Halt active motion immediately.",
        optional_parameters=(
            ParameterSpec(
                "stop_type",
                "string",
                required=False,
                description="Optional vendor-specific stop type identifier.",
            ),
        ),
    ),
    "wait_for_move_finish": CommandSpec(
        name="wait_for_move_finish",
        description="Block until the current motion completes.",
        optional_parameters=(
            ParameterSpec(
                "timeout_ms",
                "number",
                required=False,
                min_value=0,
                description="Optional timeout to guard against deadlocks.",
            ),
        ),
    ),
    "get_current_joint_position": CommandSpec(
        name="get_current_joint_position",
        description="Query joint angles and store them for later use.",
        optional_parameters=(
            ParameterSpec(
                "store_as",
                "string",
                required=False,
                description="Variable name used to store the result.",
            ),
        ),
    ),
    "get_current_cartesian_position": CommandSpec(
        name="get_current_cartesian_position",
        description="Query the current Cartesian pose.",
        optional_parameters=(
            ParameterSpec(
                "store_as",
                "string",
                required=False,
                description="Variable name used to store the result.",
            ),
        ),
    ),
    "get_robot_status": CommandSpec(
        name="get_robot_status",
        description="Query the robot status string.",
        optional_parameters=(
            ParameterSpec(
                "store_as",
                "string",
                required=False,
                description="Variable name used to store the result.",
            ),
        ),
    ),
    "set_digital_output": CommandSpec(
        name="set_digital_output",
        description="Set the state of a digital output port.",
        parameters=(
            ParameterSpec("port", "number", description="Digital output port index."),
            ParameterSpec("value", "boolean", description="Desired output value."),
        ),
    ),
    "get_digital_input": CommandSpec(
        name="get_digital_input",
        description="Read a digital input value.",
        parameters=(
            ParameterSpec("port", "number", description="Digital input port index."),
        ),
        optional_parameters=(
            ParameterSpec(
                "store_as",
                "string",
                required=False,
                description="Variable name used to store the result.",
            ),
        ),
    ),
    "set_tool_coordinate": CommandSpec(
        name="set_tool_coordinate",
        description="Set active tool frame data.",
        parameters=(
            ParameterSpec(
                "tool_data",
                "list",
                length=6,
                item_type="number",
                description="Tool frame data (x,y,z,rx,ry,rz).",
            ),
        ),
    ),
    "set_user_coordinate": CommandSpec(
        name="set_user_coordinate",
        description="Set active user frame data.",
        parameters=(
            ParameterSpec(
                "user_data",
                "list",
                length=6,
                item_type="number",
                description="User frame data (x,y,z,rx,ry,rz).",
            ),
        ),
    ),
    "grab": CommandSpec(
        name="grab",
        description="Activate end-effector to grab an object.",
    ),
    "release": CommandSpec(
        name="release",
        description="Open end-effector to release an object.",
    ),
    "print_numbers": CommandSpec(
        name="print_numbers",
        description="Diagnostic helper to print numbers via logging.",
    ),
}


LOGIC_BINARY_OPS = {"and", "or"}
COMPARISON_OPS = {"eq", "neq", "lt", "lte", "gt", "gte"}
ARITHMETIC_OPS = {"add", "minus", "multiply", "divide", "power"}
MATH_SINGLE_OPS = {"root", "abs", "neg", "ln", "log10", "exp", "pow10"}
MATH_TRIG_OPS = {"sin", "cos", "tan", "asin", "acos", "atan"}
MATH_ROUND_OPS = {"round", "roundup", "rounddown"}
MATH_CONSTANTS = {"pi", "e", "golden_ratio", "sqrt2", "sqrt1_2", "infinity"}


def validate_ir_document(ir: Dict[str, Any]) -> ValidationResult:
    """Validate an IR document and return the result."""

    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(ir, dict):
        return ValidationResult(False, ["IR document must be a JSON object."], warnings)

    version = ir.get("version")
    if version is None:
        warnings.append("IR document missing version; defaulting to 1.0")
    elif not isinstance(version, str):
        errors.append("Field 'version' must be a string if provided.")
    elif version != IR_VERSION:
        warnings.append(
            f"IR version '{version}' differs from validator version '{IR_VERSION}'."
        )

    metadata = ir.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append("Field 'metadata' must be an object when provided.")

    sequence = ir.get("sequence")
    if sequence is None:
        errors.append("IR document missing required 'sequence' array.")
        return ValidationResult(False, errors, warnings)

    if not isinstance(sequence, list):
        errors.append("Field 'sequence' must be an array of command entries.")
        return ValidationResult(False, errors, warnings)

    seen_ids: set[str] = set()
    _validate_sequence(sequence, errors, warnings, seen_ids, "sequence")

    return ValidationResult(len(errors) == 0, errors, warnings)


def _validate_parameters(
    params: Dict[str, Any],
    required_specs: Iterable[ParameterSpec],
    optional_specs: Iterable[ParameterSpec],
    context: str,
) -> List[str]:
    errors: List[str] = []
    spec_by_name: Dict[str, ParameterSpec] = {
        spec.name: spec for spec in (*required_specs, *optional_specs)
    }

    for spec in required_specs:
        if spec.name not in params:
            errors.append(f"{context}.parameters missing required field '{spec.name}'.")

    for name, value in params.items():
        if name not in spec_by_name:
            errors.append(f"{context}.parameters contains unsupported field '{name}'.")
            continue
        errors.extend(_validate_value(value, spec_by_name[name], context))

    return errors


def _validate_sequence(
    sequence: Any,
    errors: List[str],
    warnings: List[str],
    seen_ids: set[str],
    context: str,
) -> None:
    if not isinstance(sequence, list):
        errors.append(f"{context} must be an array of nodes.")
        return

    for index, node in enumerate(sequence):
        node_context = f"{context}[{index}]"
        if not isinstance(node, dict):
            errors.append(f"{node_context} must be an object.")
            continue
        _validate_node(node, errors, warnings, seen_ids, node_context)


def _validate_node(
    node: Dict[str, Any],
    errors: List[str],
    warnings: List[str],
    seen_ids: set[str],
    context: str,
) -> None:
    entry_id = node.get("id")
    if entry_id is None:
        errors.append(f"{context} missing required field 'id'.")
    elif not isinstance(entry_id, str):
        errors.append(f"{context}.id must be a string.")
    elif entry_id in seen_ids:
        errors.append(f"Duplicate node id '{entry_id}'.")
    else:
        seen_ids.add(entry_id)

    node_type = node.get("node_type")
    if node_type is None:
        errors.append(f"{context} missing required field 'node_type'.")
        return
    if not isinstance(node_type, str):
        errors.append(f"{context}.node_type must be a string.")
        return

    if node_type == "command":
        _validate_command_node(node, errors, context)
        return

    if node_type == "if":
        _validate_if_node(node, errors, warnings, seen_ids, context)
        return

    if node_type == "repeat":
        _validate_repeat_node(node, errors, warnings, seen_ids, context)
        return

    if node_type == "while":
        _validate_while_node(node, errors, warnings, seen_ids, context)
        return

    if node_type == "for_range":
        _validate_for_range_node(node, errors, warnings, seen_ids, context)
        return

    if node_type == "for_each":
        _validate_for_each_node(node, errors, warnings, seen_ids, context)
        return

    if node_type == "flow":
        _validate_flow_node(node, errors, context)
        return

    errors.append(f"{context}.node_type '{node_type}' is not supported.")


def _validate_command_node(node: Dict[str, Any], errors: List[str], context: str) -> None:
    command_name = node.get("command")
    if command_name is None:
        errors.append(f"{context} missing required field 'command'.")
        return
    if not isinstance(command_name, str):
        errors.append(f"{context}.command must be a string.")
        return

    if command_name not in COMMAND_SPECS:
        errors.append(f"{context}.command '{command_name}' is not supported.")
        return

    spec = COMMAND_SPECS[command_name]
    params = node.get("parameters", {})
    if not isinstance(params, dict):
        errors.append(f"{context}.parameters must be an object.")
    else:
        errors.extend(
            _validate_parameters(params, spec.parameters, spec.optional_parameters, context)
        )

    comment = node.get("comment")
    if comment is not None and not isinstance(comment, str):
        errors.append(f"{context}.comment must be a string when provided.")


def _validate_if_node(
    node: Dict[str, Any],
    errors: List[str],
    warnings: List[str],
    seen_ids: set[str],
    context: str,
) -> None:
    branches = node.get("branches")
    if not isinstance(branches, list) or not branches:
        errors.append(f"{context}.branches must be a non-empty array.")
    else:
        for index, branch in enumerate(branches):
            branch_context = f"{context}.branches[{index}]"
            if not isinstance(branch, dict):
                errors.append(f"{branch_context} must be an object.")
                continue
            condition = branch.get("condition")
            if condition is None:
                errors.append(f"{branch_context} missing required field 'condition'.")
            else:
                errors.extend(_validate_expression(condition, f"{branch_context}.condition"))

            body = branch.get("body", [])
            _validate_sequence(body, errors, warnings, seen_ids, f"{branch_context}.body")

    else_branch = node.get("else_branch")
    if else_branch is not None:
        _validate_sequence(else_branch, errors, warnings, seen_ids, f"{context}.else_branch")


def _validate_repeat_node(
    node: Dict[str, Any],
    errors: List[str],
    warnings: List[str],
    seen_ids: set[str],
    context: str,
) -> None:
    count = node.get("count")
    if count is None:
        errors.append(f"{context} missing required field 'count'.")
    else:
        errors.extend(_validate_expression(count, f"{context}.count"))

    body = node.get("body")
    _validate_sequence(body, errors, warnings, seen_ids, f"{context}.body")


def _validate_while_node(
    node: Dict[str, Any],
    errors: List[str],
    warnings: List[str],
    seen_ids: set[str],
    context: str,
) -> None:
    mode = node.get("mode")
    if mode not in {"while", "until"}:
        errors.append(f"{context}.mode must be either 'while' or 'until'.")

    condition = node.get("condition")
    if condition is None:
        errors.append(f"{context} missing required field 'condition'.")
    else:
        errors.extend(_validate_expression(condition, f"{context}.condition"))

    body = node.get("body")
    _validate_sequence(body, errors, warnings, seen_ids, f"{context}.body")


def _validate_for_range_node(
    node: Dict[str, Any],
    errors: List[str],
    warnings: List[str],
    seen_ids: set[str],
    context: str,
) -> None:
    variable = node.get("variable")
    if not isinstance(variable, str) or not variable:
        errors.append(f"{context}.variable must be a non-empty string.")

    for field in ("from", "to", "by"):
        expr = node.get(field)
        if expr is None:
            errors.append(f"{context} missing required field '{field}'.")
        else:
            errors.extend(_validate_expression(expr, f"{context}.{field}"))

    body = node.get("body")
    _validate_sequence(body, errors, warnings, seen_ids, f"{context}.body")


def _validate_for_each_node(
    node: Dict[str, Any],
    errors: List[str],
    warnings: List[str],
    seen_ids: set[str],
    context: str,
) -> None:
    variable = node.get("variable")
    if not isinstance(variable, str) or not variable:
        errors.append(f"{context}.variable must be a non-empty string.")

    collection = node.get("collection")
    if collection is None:
        errors.append(f"{context} missing required field 'collection'.")
    else:
        errors.extend(_validate_expression(collection, f"{context}.collection"))

    body = node.get("body")
    _validate_sequence(body, errors, warnings, seen_ids, f"{context}.body")


def _validate_flow_node(node: Dict[str, Any], errors: List[str], context: str) -> None:
    flow = node.get("flow")
    if flow not in {"break", "continue"}:
        errors.append(f"{context}.flow must be either 'break' or 'continue'.")


def _validate_expression(expr: Any, context: str) -> List[str]:
    errors: List[str] = []
    if not isinstance(expr, dict):
        return [f"{context} must be an object."]

    expr_type = expr.get("expr_type")
    if expr_type is None:
        return [f"{context} missing required field 'expr_type'."]
    if not isinstance(expr_type, str):
        return [f"{context}.expr_type must be a string."]

    if expr_type == "literal_number":
        value = expr.get("value")
        if not isinstance(value, Number) or isinstance(value, bool):
            errors.append(f"{context}.value must be a number.")
        return errors

    if expr_type == "literal_boolean":
        if not isinstance(expr.get("value"), bool):
            errors.append(f"{context}.value must be a boolean.")
        return errors

    if expr_type == "literal_null":
        return errors

    if expr_type == "comparison":
        op = expr.get("op")
        if op not in COMPARISON_OPS:
            errors.append(f"{context}.op must be one of {sorted(COMPARISON_OPS)}.")
        errors.extend(_validate_expression(expr.get("left"), f"{context}.left"))
        errors.extend(_validate_expression(expr.get("right"), f"{context}.right"))
        return errors

    if expr_type == "logic_binary":
        op = expr.get("op")
        if op not in LOGIC_BINARY_OPS:
            errors.append(f"{context}.op must be one of {sorted(LOGIC_BINARY_OPS)}.")
        errors.extend(_validate_expression(expr.get("left"), f"{context}.left"))
        errors.extend(_validate_expression(expr.get("right"), f"{context}.right"))
        return errors

    if expr_type == "logic_not":
        errors.extend(_validate_expression(expr.get("argument"), f"{context}.argument"))
        return errors

    if expr_type == "ternary":
        errors.extend(_validate_expression(expr.get("condition"), f"{context}.condition"))
        errors.extend(_validate_expression(expr.get("when_true"), f"{context}.when_true"))
        errors.extend(_validate_expression(expr.get("when_false"), f"{context}.when_false"))
        return errors

    if expr_type == "arithmetic":
        op = expr.get("op")
        if op not in ARITHMETIC_OPS:
            errors.append(f"{context}.op must be one of {sorted(ARITHMETIC_OPS)}.")
        errors.extend(_validate_expression(expr.get("left"), f"{context}.left"))
        errors.extend(_validate_expression(expr.get("right"), f"{context}.right"))
        return errors

    if expr_type == "math_single":
        op = expr.get("op")
        if op not in MATH_SINGLE_OPS:
            errors.append(f"{context}.op must be one of {sorted(MATH_SINGLE_OPS)}.")
        errors.extend(_validate_expression(expr.get("argument"), f"{context}.argument"))
        return errors

    if expr_type == "math_trig":
        op = expr.get("op")
        if op not in MATH_TRIG_OPS:
            errors.append(f"{context}.op must be one of {sorted(MATH_TRIG_OPS)}.")
        errors.extend(_validate_expression(expr.get("argument"), f"{context}.argument"))
        return errors

    if expr_type == "math_constant":
        constant = expr.get("constant")
        if constant not in MATH_CONSTANTS:
            errors.append(f"{context}.constant must be one of {sorted(MATH_CONSTANTS)}.")
        return errors

    if expr_type == "math_round":
        op = expr.get("op")
        if op not in MATH_ROUND_OPS:
            errors.append(f"{context}.op must be one of {sorted(MATH_ROUND_OPS)}.")
        errors.extend(_validate_expression(expr.get("argument"), f"{context}.argument"))
        return errors

    if expr_type == "math_modulo":
        errors.extend(_validate_expression(expr.get("left"), f"{context}.left"))
        errors.extend(_validate_expression(expr.get("right"), f"{context}.right"))
        return errors

    if expr_type == "math_constrain":
        errors.extend(_validate_expression(expr.get("value"), f"{context}.value"))
        errors.extend(_validate_expression(expr.get("low"), f"{context}.low"))
        errors.extend(_validate_expression(expr.get("high"), f"{context}.high"))
        return errors

    if expr_type == "math_random_int":
        errors.extend(_validate_expression(expr.get("low"), f"{context}.low"))
        errors.extend(_validate_expression(expr.get("high"), f"{context}.high"))
        return errors

    if expr_type == "math_random_float":
        return errors

    errors.append(f"{context}.expr_type '{expr_type}' is not supported.")
    return errors

def _validate_value(value: Any, spec: ParameterSpec, context: str) -> List[str]:
    path = f"{context}.parameters.{spec.name}"
    expected = spec.value_type

    if expected == "string":
        if not isinstance(value, str):
            return [f"{path} must be a string."]
        return []

    if expected == "boolean":
        if not isinstance(value, bool):
            return [f"{path} must be a boolean."]
        return []

    if expected == "number":
        if not isinstance(value, Number) or isinstance(value, bool):
            return [f"{path} must be a number."]
        return _check_numeric_bounds(value, spec, path)

    if expected == "list":
        if not isinstance(value, list):
            return [f"{path} must be an array."]
        if spec.length is not None and len(value) != spec.length:
            return [f"{path} must contain exactly {spec.length} items."]
        if spec.item_type is not None:
            item_errors: List[str] = []
            for idx, item in enumerate(value):
                item_path = f"{path}[{idx}]"
                pseudo_spec = ParameterSpec(
                    name=item_path,
                    value_type=spec.item_type,
                    required=True,
                    min_value=spec.min_value,
                    max_value=spec.max_value,
                )
                item_errors.extend(_validate_value(item, pseudo_spec, context))
            return item_errors
        return []

    if expected == "cartesian_point":
        return _validate_cartesian_point(value, path)

    return [f"{path} has unknown parameter type '{expected}'."]


def _check_numeric_bounds(value: Number, spec: ParameterSpec, path: str) -> List[str]:
    errors: List[str] = []
    if spec.min_value is not None and value < spec.min_value:
        errors.append(f"{path} must be >= {spec.min_value}.")
    if spec.max_value is not None and value > spec.max_value:
        errors.append(f"{path} must be <= {spec.max_value}.")
    return errors


def _validate_cartesian_point(value: Any, path: str) -> List[str]:
    if not isinstance(value, dict):
        return [f"{path} must be an object with keys {CARTESIAN_FIELDS}."]

    errors: List[str] = []
    for field in CARTESIAN_FIELDS:
        if field not in value:
            errors.append(f"{path} missing required field '{field}'.")
            continue
        coord_value = value[field]
        if not isinstance(coord_value, Number) or isinstance(coord_value, bool):
            errors.append(f"{path}.{field} must be a number.")
    return errors


def pretty_print_spec() -> str:
    """Return a human-readable summary of supported commands."""

    lines: List[str] = ["Robot Workflow IR Specification", "===============================", ""]
    for command in sorted(COMMAND_SPECS.values(), key=lambda s: s.name):
        lines.append(f"- {command.name}: {command.description}")
        all_params = list(command.parameters) + list(command.optional_parameters)
        if not all_params:
            continue
        for param in all_params:
            requirement = "required" if param.required else "optional"
            info = f"    • {param.name} ({param.value_type}, {requirement})"
            bounds: List[str] = []
            if param.min_value is not None:
                bounds.append(f">= {param.min_value}")
            if param.max_value is not None:
                bounds.append(f"<= {param.max_value}")
            if param.length is not None:
                bounds.append(f"length == {param.length}")
            if param.item_type is not None:
                bounds.append(f"items: {param.item_type}")
            if bounds:
                info += " [" + ", ".join(bounds) + "]"
            if param.description:
                info += f" — {param.description}"
            lines.append(info)
        lines.append("")
    return "\n".join(lines)


__all__ = [
    "IR_VERSION",
    "COMMAND_SPECS",
    "ValidationResult",
    "ParameterSpec",
    "CommandSpec",
    "validate_ir_document",
    "pretty_print_spec",
]
