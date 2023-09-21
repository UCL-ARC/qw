"""Basic definitions."""


class QwError(RuntimeError):
    """
    Application error.

    Exception that will be caught and whose message will be displayed
    to the user (without a stack trace).
    """
