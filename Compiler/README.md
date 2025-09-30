# Robot Workflow IR (Intermediate Representation)

This package defines the JSON-based IR that bridges the visual Blockly editor
and the C#/RobotLib execution layer. The structure is intentionally close to
the `BaseRobot` interface so each IR command maps one-to-one to an available
robot action.

## Document layout

```json
{
  "version": "1.0",
  "metadata": { "robot_brand": "fanuc", "created_by": "..." },
  "sequence": [
    {
      "id": "unique_block_id",
      "command": "move_linear",
      "parameters": {
        "x": 100,
        "y": 200,
        "z": 300,
        "rx": 0,
        "ry": 180,
        "rz": 90,
        "speed_percentage": 40
      },
      "comment": "Optional human-readable note"
    }
  ]
}
```

- `version`: optional string. The validator currently emits warnings if it
  differs from the library version (`1.0`).
- `metadata`: optional object carrying free-form details (e.g. blockly project
  name, robot brand, author, timestamps).
- `sequence`: ordered list of commands. Each command must have:
  - `id`: unique string (re-use Blockly block IDs to simplify traceability).
  - `command`: name from the supported command set (see below).
  - `parameters`: object containing the inputs required by that command.
  - `comment`: optional annotation shown to engineers or used in generated
    source comments.

## Supported commands

Run `python3 -c "from Compiler.ir_schema import pretty_print_spec; print(pretty_print_spec())"`
to display the full command list with parameter descriptions. The mapping
follows the methods in `RobotLib.BaseRobot` and includes utility operations
like `set_speed`, `move_linear`, `move_joint`, `grab`, `release`, and query
commands (`get_current_joint_position`, `get_robot_status`, etc.).

Special parameter shapes:

- Cartesian points (`move_circular`) expect objects with keys `x`, `y`, `z`,
  `rx`, `ry`, `rz`.
- Tool/User coordinates expect arrays of six numbers `[x, y, z, rx, ry, rz]`.
- Percentage inputs are constrained to the range 0–100.
- Query commands that return values accept an optional `store_as` string so the
  downstream pipeline can track variables during code generation.

## Blockly integration checklist

1. **Generator output**: Instead of emitting Python code, make each Blockly
   block emit a JSON snippet that follows the schema above. Serialize the full
   workflow to a single document containing the ordered `sequence` array.
2. **Block IDs**: Use the Blockly block ID (`block.id`) as the IR `id` field to
   simplify round-tripping errors back to the UI (`showErrorInBlockly`).
3. **Transport**: Send the resulting JSON through `QWebChannel` (e.g.
   `updatePythonCode(irJson)`), keeping communication asynchronous-safe. The
   PyQt handler can immediately feed the JSON into `validate_ir_document` to
   surface structured error messages.
4. **Error reporting**: When validation fails, return the offending `id` and a
   user-friendly message back to JavaScript, so the block can be highlighted.
5. **Extensibility**: If a new robot capability is required, add it to
   `COMMAND_SPECS` and update the Blockly block definition so both sides stay
   in sync.

## Sample

A ready-to-use example is available in `sample_ir.json`. Validate it with:

```bash
python3 - <<'PY'
import json
from Compiler.ir_schema import validate_ir_document

with open('Compiler/sample_ir.json', 'r', encoding='utf-8') as fh:
    document = json.load(fh)

result = validate_ir_document(document)
print('valid:', result.valid)
print('errors:', result.errors)
print('warnings:', result.warnings)
PY
```

This validation step is designed to run inside the PyQt backend whenever the
front-end sends updated IR data.

## C# code generation

The generator uses Jinja2 to transform IR documents directly into C# code that
targets the `RobotLib` classes.

1. Install the dependency (once): `pip install jinja2`
2. Run the generator via the CLI wrapper:

   ```bash
   python3 -m Compiler.codegen Compiler/sample_ir.json -o generated_workflow.cs
   ```

   Use `--template-dir <path>` to supply custom Jinja2 templates if the default
   `templates/workflow.cs.j2` layout needs adjustments.

3. Review the emitted C# source (a sample is provided in
   `Compiler/sample_output.cs`), add it to your solution, and reference the
   appropriate RobotLib brand DLL so the generated code compiles.

The CLI validates the IR before rendering; schema errors are reported with the
same identifiers used in Blockly, making it straightforward to highlight the
offending block in the UI.
