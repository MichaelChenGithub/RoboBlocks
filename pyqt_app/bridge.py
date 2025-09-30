"""PyQt6 bridge that relays Blockly IR JSON to the compiler pipeline."""
from __future__ import annotations

import json

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from Compiler.codegen import CodeGenerationError, generate_csharp_source
from Compiler.ir_schema import ValidationResult, validate_ir_document


class RobotCompilerBridge(QObject):
    """Expose slots/signals for the web view to interact with the compiler."""

    validationResult = pyqtSignal(bool, list, list)
    generationFailed = pyqtSignal(str)
    codeGenerated = pyqtSignal(str)
    irUpdated = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._last_source: str = ""
        self._last_ir_json: str = ""

    @pyqtSlot(str)
    def updateIrJson(self, ir_json: str) -> None:
        """Receive IR JSON from JavaScript, validate, and compile."""

        self._last_ir_json = ir_json
        self.irUpdated.emit(ir_json)

        try:
            document = json.loads(ir_json)
        except json.JSONDecodeError as exc:
            self.validationResult.emit(False, [f"Invalid JSON: {exc}"], [])
            return

        validation: ValidationResult = validate_ir_document(document)
        if not validation.valid:
            self.validationResult.emit(False, list(validation.errors), list(validation.warnings))
            return

        self.validationResult.emit(True, [], list(validation.warnings))

        try:
            source = generate_csharp_source(document)
        except CodeGenerationError as exc:
            self.generationFailed.emit(str(exc))
            return

        self._last_source = source
        self.codeGenerated.emit(source)

    @pyqtSlot(result=str)
    def currentSource(self) -> str:
        """Return the most recently generated source."""

        return self._last_source

    @pyqtSlot(str, result=bool)
    def saveSourceToFile(self, path: str) -> bool:
        """Persist the current source to disk."""

        if not self._last_source:
            return False
        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(self._last_source)
        except OSError:
            return False
        return True


__all__ = ["RobotCompilerBridge"]
