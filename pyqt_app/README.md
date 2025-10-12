# PyQt6 Frontend

This desktop UI embeds the Blockly editor (via `QWebEngineView`) and mirrors the
generated Python code into a side panel for inspection or saving.

## Requirements

Install the Python dependencies first:

```bash
pip install PyQt6 PyQt6-WebEngine
```

## Running the app

```bash
python3 -m pyqt_app.main
```

The bundled `resources/blockly_app.html` hosts a Blockly workspace with the
toolbox defined in `robot_blocks.js`. `robot_python_generator.js` adds Python
emitters for each custom block so that movements, IO, and CV actions map to the
appropriate `Robot` or `CVModel` instances. Start every program with the
`Main → main_entry` block; only statements nested under that entry point are
included in the generated script. The `connect_robot` block also lets you pick
the robot brand while wiring up the runtime. On every workspace change it calls
`Blockly.Python.workspaceToCode(...)` and forwards the resulting source through
the Qt bridge.

## Bridge API

Slots exposed to JavaScript:

- `robotBridge.updatePythonCode(source: str)` – accept Python text generated in
  JavaScript.
- `robotBridge.currentSource()` – return the most recent Python source.
- `robotBridge.saveSourceToFile(path: str)` – persist the current source to
  disk.

Signals emitted from Python:

- `pythonCodeUpdated(source: str)` – notifies listeners whenever new Python code
  arrives.

Extend `robot_blocks.js` with additional block definitions as needed and add
matching generator handlers in `robot_python_generator.js`.

The generated Python assumes the helper package `tools` is on the import path.
It provides `tools.robot.Robot` and `tools.vision.CVModel`, both of which emit
console output so you can observe the sequence of actions.

Use the **Run** toolbar action to execute the current Python program inside a
background thread. Output from the run appears in the terminal view beneath the
code editor.
