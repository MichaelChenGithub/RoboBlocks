"""Compiler package exposing IR validation and C# generation utilities."""

from .ir_schema import (
    COMMAND_SPECS,
    IR_VERSION,
    ValidationResult,
    pretty_print_spec,
    validate_ir_document,
)
from .codegen import (
    CodeGenerationError,
    generate_csharp_project,
    generate_csharp_source,
    generate_from_file,
)

__all__ = [
    "COMMAND_SPECS",
    "IR_VERSION",
    "ValidationResult",
    "pretty_print_spec",
    "validate_ir_document",
    "CodeGenerationError",
    "generate_csharp_source",
    "generate_csharp_project",
    "generate_from_file",
]
