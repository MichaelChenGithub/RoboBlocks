# PyQt6 Frontend

This desktop UI hosts the Blockly editor (via `QWebEngineView`) and forwards IR
JSON to the compiler pipeline.

## Requirements

Install the Python dependencies first:

```bash
pip install PyQt6 PyQt6-WebEngine jinja2
```

## Running the app

```bash
python3 -m pyqt_app.main
```

The bundled `resources/blockly_app.html` hosts a Blockly workspace with custom
blocks that mirror `RobotLib.BaseRobot`. It automatically streams the generated
IR JSON to the backend on every change. Adapt the block definitions or toolbox
layout in `robot_blocks.js` and `robot_generator.js` as your workflow evolves.

## JavaScript API

The bridge currently provides:

- `robotBridge.updateIrJson(jsonString)` – validate and compile the supplied IR
  document. Results are delivered through signals.
- `robotBridge.currentSource()` – fetch the latest generated C# text.
- `robotBridge.saveSourceToFile(path)` – ask the backend to write the source to
  disk.

Signals exposed to JavaScript:

- `validationResult(isValid: bool, errors: list[str], warnings: list[str])`
- `codeGenerated(source: str)` – emits the raw C# string.
- `generationFailed(message: str)` – emitted if C# generation fails after a
  successful validation.

Update your Blockly generator to call `robotBridge.updateIrJson(...)` whenever
blocks change. The PyQt status bar and the right-hand log panel will reflect the
validation state, and the generated C# appears inside the desktop app for quick
review or saving.
