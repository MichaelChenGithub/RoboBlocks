"""PyQt6 application hosting Blockly via QWebEngine and the compiler bridge."""
from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import QThread, QUrl, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QSplitter,
)

# Import QAction and other GUI-related classes from QtGui
from PyQt6.QtGui import QAction

from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineWidgets import QWebEngineView

from .bridge import RobotCompilerBridge
from .executor import PythonExecutionWorker


_RESOURCE_DIR = Path(__file__).parent / "resources"
_HTML_ENTRY = _RESOURCE_DIR / "blockly_app.html"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Blockly Python Generator")
        self.resize(1280, 800)

        self._bridge = RobotCompilerBridge()
        self._runner_thread: QThread | None = None
        self._runner_worker: PythonExecutionWorker | None = None
        self._run_action: QAction | None = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        self._web_view = QWebEngineView(self)
        self._code_view = QPlainTextEdit(self)
        self._code_view.setReadOnly(True)
        self._code_view.setPlaceholderText("Python code will appear here once the workspace changes.")
        self._terminal_view = QPlainTextEdit(self)
        self._terminal_view.setReadOnly(True)
        self._terminal_view.setPlaceholderText("Execution output will appear here.")

        splitter = QSplitter(self)
        splitter.addWidget(self._web_view)
        code_panel = QSplitter(Qt.Orientation.Vertical, self)
        code_panel.addWidget(self._code_view)
        code_panel.addWidget(self._terminal_view)
        code_panel.setStretchFactor(0, 3)
        code_panel.setStretchFactor(1, 2)
        splitter.addWidget(code_panel)
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
        save_action = QAction("Save Python...", self)
        save_action.triggered.connect(self._save_source)
        toolbar.addAction(save_action)

        run_action = QAction("Run", self)
        run_action.triggered.connect(self._run_code)
        toolbar.addAction(run_action)
        self._run_action = run_action

    def _connect_signals(self) -> None:
        self._bridge.pythonCodeUpdated.connect(self._on_python_code_updated)

    def _on_python_code_updated(self, source: str) -> None:
        self._code_view.setPlainText(source)
        if source.strip():
            self.statusBar().showMessage("Python code updated")
        else:
            self.statusBar().showMessage("Workspace empty")

    def _save_source(self) -> None:
        source = self._bridge.currentSource()
        if not source:
            QMessageBox.information(self, "Save Python", "No generated code to save yet.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Generated Python",
            str(Path.cwd() / "generated_workflow.py"),
            "Python Files (*.py);;All Files (*)",
        )
        if not path:
            return
        if not self._bridge.saveSourceToFile(path):
            QMessageBox.critical(self, "Save Python", "Failed to write file.")
        else:
            self.statusBar().showMessage(f"Saved to {path}")

    def _run_code(self) -> None:
        if self._runner_thread is not None:
            QMessageBox.information(self, "Run Python", "Execution already in progress.")
            return

        source = self._bridge.currentSource()
        if not source.strip():
            QMessageBox.information(self, "Run Python", "No generated code to run.")
            return

        self._terminal_view.clear()
        self.statusBar().showMessage("Running Python program…")
        if self._run_action:
            self._run_action.setEnabled(False)

        self._runner_thread = QThread(self)
        self._runner_worker = PythonExecutionWorker()
        self._runner_worker.moveToThread(self._runner_thread)
        self._runner_worker.outputProduced.connect(self._append_terminal)
        self._runner_worker.executionFinished.connect(self._on_execution_finished)
        self._runner_thread.finished.connect(self._cleanup_runner)

        # Ensure the code string is passed once the thread starts.
        self._runner_thread.started.connect(lambda: self._runner_worker.run_code(source))
        self._runner_thread.start()

    def _append_terminal(self, text: str) -> None:
        if text:
            self._terminal_view.appendPlainText(text.rstrip("\n"))

    def _on_execution_finished(self, success: bool) -> None:
        message = "Execution finished" if success else "Execution failed"
        self.statusBar().showMessage(message)
        if self._run_action:
            self._run_action.setEnabled(True)
        if self._runner_thread:
            self._runner_thread.quit()

    def _cleanup_runner(self) -> None:
        if self._runner_worker is not None:
            self._runner_worker.deleteLater()
            self._runner_worker = None
        if self._runner_thread is not None:
            self._runner_thread.deleteLater()
            self._runner_thread = None


def run() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":  # pragma: no cover - GUI entry point
    raise SystemExit(run())
