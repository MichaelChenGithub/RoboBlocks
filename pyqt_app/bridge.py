"""PyQt6 bridge that relays Blockly-generated Python source to the desktop UI."""
from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot


class RobotCompilerBridge(QObject):
    """Expose slots/signals for exchanging generated Python code with the web view."""

    pythonCodeUpdated = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._last_source = ""

    @pyqtSlot(str)
    def updatePythonCode(self, python_source: str) -> None:
        """Receive Python source from JavaScript and broadcast it to the desktop UI."""

        self._last_source = python_source or ""
        self.pythonCodeUpdated.emit(self._last_source)

    @pyqtSlot(result=str)
    def currentSource(self) -> str:
        """Return the most recently generated Python source."""

        return self._last_source

    @pyqtSlot(str, result=bool)
    def saveSourceToFile(self, path: str) -> bool:
        """Persist the current Python source to disk."""

        if not self._last_source:
            return False

        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(self._last_source)
        except OSError:
            return False
        return True


__all__ = ["RobotCompilerBridge"]
