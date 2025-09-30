"""PyQt6 application hosting Blockly via QWebEngine and the compiler bridge."""
from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QSplitter,
)

# Import QAction and other GUI-related classes from QtGui
from PyQt6.QtGui import QAction, QIcon 

from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineWidgets import QWebEngineView

from .bridge import RobotCompilerBridge


_RESOURCE_DIR = Path(__file__).parent / "resources"
_HTML_ENTRY = _RESOURCE_DIR / "blockly_app.html"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Robot Workflow Compiler")
        self.resize(1280, 800)

        self._bridge = RobotCompilerBridge()
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        self._web_view = QWebEngineView(self)
        self._ir_view = QPlainTextEdit(self)
        self._ir_view.setReadOnly(True)
        self._ir_view.setPlaceholderText("IR JSON will appear here once the workspace changes.")
        self._code_view = QPlainTextEdit(self)
        self._code_view.setReadOnly(True)

        splitter = QSplitter(self)
        splitter.addWidget(self._web_view)
        side_panel = QSplitter(Qt.Orientation.Vertical, self)
        side_panel.addWidget(self._ir_view)
        side_panel.addWidget(self._code_view)
        side_panel.setStretchFactor(0, 1)
        side_panel.setStretchFactor(1, 1)
        splitter.addWidget(side_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        self.setCentralWidget(splitter)

        channel = QWebChannel(self._web_view.page())
        channel.registerObject("robotBridge", self._bridge)
        self._web_view.page().setWebChannel(channel)

        self.statusBar().showMessage("Ready")

        if _HTML_ENTRY.exists():
            self._web_view.load(QUrl.fromLocalFile(str(_HTML_ENTRY.resolve())))
        else:
            self.statusBar().showMessage("Missing frontend HTML entry point.")

        toolbar = self.addToolBar("Main")
        save_action = QAction("Save C#...", self)
        save_action.triggered.connect(self._save_source)
        toolbar.addAction(save_action)

    def _connect_signals(self) -> None:
        self._bridge.validationResult.connect(self._on_validation_result)
        self._bridge.codeGenerated.connect(self._on_code_generated)
        self._bridge.generationFailed.connect(self._on_generation_failed)
        self._bridge.irUpdated.connect(self._on_ir_updated)

    def _on_validation_result(self, is_valid: bool, errors: list, warnings: list) -> None:
        if is_valid:
            if warnings:
                self.statusBar().showMessage("Valid IR (warnings logged)")
            else:
                self.statusBar().showMessage("Valid IR")
        else:
            message = errors[0] if errors else "Validation failed"
            self.statusBar().showMessage(message)

    def _on_code_generated(self, source: str) -> None:
        self._code_view.setPlainText(source)
        self.statusBar().showMessage("C# source generated")

    def _on_generation_failed(self, message: str) -> None:
        self.statusBar().showMessage("Generation failed")
        QMessageBox.critical(self, "Generation Error", message)

    def _on_ir_updated(self, ir_json: str) -> None:
        self._ir_view.setPlainText(ir_json)

    def _save_source(self) -> None:
        source = self._bridge.currentSource()
        if not source:
            QMessageBox.information(self, "Save C#", "No generated code to save yet.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Generated C#",
            str(Path.cwd() / "generated_workflow.cs"),
            "C# Files (*.cs);;All Files (*)",
        )
        if not path:
            return
        if not self._bridge.saveSourceToFile(path):
            QMessageBox.critical(self, "Save C#", "Failed to write file.")
        else:
            self.statusBar().showMessage(f"Saved to {path}")


def run() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":  # pragma: no cover - GUI entry point
    raise SystemExit(run())
