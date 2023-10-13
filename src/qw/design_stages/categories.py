"""Categories used in design stages, expect this will mostly be enums."""
from enum import Enum


class DesignStage(str, Enum):
    """Git hosting service identifiers."""

    NEED = "user-need"
    INPUT = "design-input"
    OUTPUT = "design-output"
    VERIFICATION = "verification"
    VALIDATION = "validation"


class RemoteItemType(str, Enum):
    """Remote repository item type."""

    ISSUE = "issue"
    REQUEST = "request"
