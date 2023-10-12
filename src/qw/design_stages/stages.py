"""All design stage types."""
from enum import Enum


class DesignStage(str, Enum):
    """Git hosting service identifiers."""

    NEED = "user-need"
    INPUT = "design-input"
    OUTPUT = "design-output"
    VERIFICATION = "verification"
    VALIDATION = "validation"
