"""Background execution helpers for running generated Python code."""
from __future__ import annotations

import io
import traceback
from contextlib import redirect_stderr, redirect_stdout

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot


class PythonExecutionWorker(QObject):
    """Run arbitrary Python source inside a background thread."""

    outputProduced = pyqtSignal(str)
    executionFinished = pyqtSignal(bool)

    @pyqtSlot(str)
    def run_code(self, source: str) -> None:
        buffer = io.StringIO()
        success = True
        try:
            namespace: dict[str, object] = {"__name__": "__main__"}
            with redirect_stdout(buffer), redirect_stderr(buffer):
                exec(source, namespace, namespace)
        except Exception:
            success = False
            buffer.write("\n")
            buffer.write(traceback.format_exc())
        text = buffer.getvalue()
        if text:
            self.outputProduced.emit(text)
        self.executionFinished.emit(success)
