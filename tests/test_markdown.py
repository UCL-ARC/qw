"""Testing markdown processing.."""
from pathlib import Path

from qw.md import text_under_heading


def test_read_markdown():
    """Quick and dirty test to ensure."""
    file = Path(__file__).parent / "resources" / "test_issue.md"
    output = text_under_heading(file.read_text(), "What happened?")
    assert output == "A bug happened!\nOn multiple lines\nHere we go"
