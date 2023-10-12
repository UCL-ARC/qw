"""Testing markdown processing.."""
from pathlib import Path

import pytest

from qw.base import QwError
from qw.md import text_under_heading


def test_read_markdown():
    """Quick and dirty test to ensure."""
    file = Path(__file__).parent / "resources" / "markdown" / "test_issue.md"
    output = text_under_heading(file.read_text(), "What happened?")
    assert output == "A bug happened!\nOn multiple lines\nHere we go"


def test_no_header_found():
    """Ensure exception raised if header not found."""
    file = Path(__file__).parent / "resources" / "markdown" / "test_issue.md"
    non_existent_heading = "I really don't exist"

    with pytest.raises(QwError) as exception_info:
        text_under_heading(file.read_text(), non_existent_heading)
    assert non_existent_heading in str(exception_info.value)
