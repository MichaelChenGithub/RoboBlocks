"""PyQt6 bridge that relays Blockly IR JSON to the compiler pipeline."""
from __future__ import annotations

import json
import re
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from Compiler.codegen import (
    CodeGenerationError,
    generate_csharp_project,
    generate_csharp_source,
)
from Compiler.ir_schema import ValidationResult, validate_ir_document


class RobotCompilerBridge(QObject):
    """Expose slots/signals for the web view to interact with the compiler."""

    validationResult = pyqtSignal(bool, list, list)
    generationFailed = pyqtSignal(str)
    codeGenerated = pyqtSignal(str)
    irUpdated = pyqtSignal(str)
    projectGenerated = pyqtSignal(str, str)
    projectGenerationFailed = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._last_source: str = ""
        self._last_ir_json: str = ""
        self._last_document: dict | None = None

    @pyqtSlot(str)
    def updateIrJson(self, ir_json: str) -> None:
        """Receive IR JSON from JavaScript, validate, and compile."""

        self._last_ir_json = ir_json
        self._last_document = None
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
        self._last_document = document
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

    @pyqtSlot(str, result=bool)
    def exportProjectBundle(self, destination: str) -> bool:
        """Write the generated C# source and project files to the target folder."""

        if not self._last_document:
            self.projectGenerationFailed.emit("No valid IR available. Generate code first.")
            return False

        try:
            target_dir = Path(destination).expanduser()
        except (OSError, RuntimeError, ValueError):
            self.projectGenerationFailed.emit("Invalid destination path.")
            return False

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self.projectGenerationFailed.emit(f"Failed to prepare destination: {exc}")
            return False

        metadata = self._last_document.get("metadata", {}) or {}
        class_stem = self._safe_stem(metadata.get("class_name"), "RobotProgram")
        assembly_stem = self._safe_stem(
            metadata.get("assembly_name") or metadata.get("class_name"),
            "RobotProgram",
        )

        source_path = target_dir / f"{class_stem}.cs"
        project_path = target_dir / f"{assembly_stem}.csproj"

        try:
            source_text = generate_csharp_source(self._last_document)
            project_text = generate_csharp_project(self._last_document)
            source_path.write_text(source_text, encoding="utf-8")
            project_path.write_text(project_text, encoding="utf-8")
        except (CodeGenerationError, OSError, RuntimeError) as exc:
            self.projectGenerationFailed.emit(str(exc))
            return False

        self.projectGenerated.emit(str(project_path), str(source_path))
        return True

    @staticmethod
    def _safe_stem(candidate: str | None, fallback: str) -> str:
        text = candidate or ""
        stem = re.sub(r"[^0-9A-Za-z_-]", "_", text).strip("._")
        return stem or fallback


__all__ = ["RobotCompilerBridge"]
