"""Testing markdown processing.."""
from abc import abstractmethod
from pathlib import Path
from typing import Self

import pytest

from qw.base import QwError
from qw.md import DocumentBuilder, text_under_heading

BOLD = DocumentBuilder.Boldness.BOLD
ITALIC = DocumentBuilder.Italicness.ITALIC
PRE = DocumentBuilder.Spacing.MONOSPACED
LISTO = DocumentBuilder.ParagraphType.LIST_ORDERED
LISTU = DocumentBuilder.ParagraphType.LIST_UNORDERED
FENCED = DocumentBuilder.ParagraphType.PREFORMATTED


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


def test_markdown_normal_paragraph():
    """Test the generation of a single normal paragraph."""
    Generates().paragraph().text("Hello, ").text(
        "this",
        bold=BOLD,
    ).text(
        " is a ",
    ).text("markdown", italic=ITALIC).text(
        ". It can use ",
    ).text(
        "underscore",
        italic=ITALIC,
    ).text(
        " ",
    ).text(
        "format",
        bold=BOLD,
    ).text(
        " as well.",
    ).ends().from_markdown(
        "Hello, **this** is a *markdown*. "
        "It can use _underscore_ __format__ as well.",
    )


def test_markdown_list():
    """Test the generation of a markdown list."""
    Generates().paragraph().text("A list:").paragraph(
        LISTO,
        0,
    ).text(
        "Numbered point",
    ).paragraph(LISTO, 0).text("Another ").text("numbered", bold=BOLD).text(
        " point",
    ).paragraph(
        LISTU,
        1,
    ).text(
        "bullet",
    ).paragraph(
        LISTU,
        1,
    ).text(
        "another bullet",
    ).paragraph(
        LISTU,
        2,
    ).text(
        "deeper",
    ).paragraph(
        LISTU,
        1,
    ).text(
        "back to ",
    ).text(
        "1",
        italic=ITALIC,
    ).paragraph(
        LISTO,
        2,
    ).text(
        "deeper again",
    ).paragraph(
        LISTO,
        0,
    ).text(
        "Last",
    ).ends().from_markdown(
        """A list:
1. Numbered point
2. Another **numbered** point
    * bullet
    * another bullet
      * deeper
    * back to _1_
      1. deeper again
3. Last
""",
    )


def test_markdown_pre():
    """Test markdown fences and backticks."""
    Generates().paragraph().text("Some ").text(
        "code",
        pre=PRE,
    ).paragraph(FENCED).text(
        'int main(int argc, char** argv) {\n    printf("Hello world!");\n}',
    ).paragraph().text("that is in C.").paragraph(FENCED).text(
        'def main():\n    print("Hello world!")',
    ).paragraph().text(
        "and some that's in Python.",
    ).ends().from_markdown(
        """Some `code`

```
int main(int argc, char** argv) {
    printf("Hello world!");
}
```

that is in C.

~~~~~~python
def main():
    print("Hello world!")
~~~~

and some that's in Python.
""",
    )


class Generates(DocumentBuilder):
    """Builder for Markdown tester."""

    def __init__(self):
        """Markdown test builder."""
        self.next_test = None
        self.last = self

    def from_markdown(self, markdown):
        """Test that markdown satisfies the tests in order."""
        self.current = self
        self.render_markdown(markdown)

    def text(
        self,
        text: str,
        bold: DocumentBuilder.Boldness | None = None,
        italic: DocumentBuilder.Italicness | None = None,
        pre: DocumentBuilder.Spacing | None = None,
    ) -> Self:
        """Test that markdown has a text run next."""
        self.last.next_test = ChecksText(text, bold, italic, pre)
        self.last = self.last.next_test
        return self

    def hyperlink(self, text: str, link: str) -> Self:
        """Test that markdown has a link next."""
        self.last.next_test = ChecksLink(text, link)
        self.last = self.last.next_test
        return self

    def paragraph(
        self,
        paragraph_type: DocumentBuilder.ParagraphType = None,
        paragraph_level: int = 0,
    ) -> Self:
        """Test that markdown opens a paragaph next."""
        self.last.next_test = ChecksParagraph(paragraph_type, paragraph_level)
        self.last = self.last.next_test
        return self

    def ends(self) -> Self:
        """Test that the markdown ends now."""
        self.last.next_test = ChecksEnd()
        self.last = self.last.next_test
        return self

    def _get_next(self):
        self.current = self.current.next_test
        assert self.current is not None, "Ran out of tests"
        return self.current

    def new_paragraph(self, paragraph_type=None, paragraph_level=0):
        """Pass the paragraph open to the current tester."""
        self._get_next().new_paragraph(paragraph_type, paragraph_level)

    def add_run(self, text, bold=None, italic=None, pre=None):
        """Pass the text run to the current tester."""
        self._get_next().add_run(text, bold, italic, pre)

    def add_hyperlink(self, text, link):
        """Pass the link to the current tester."""
        self._get_next().add_hyperlink(text, link)

    def end(self):
        """Pass the end to the current tester."""
        self._get_next().end()


class Checks(Generates):
    """Tester base class that fails no matter what is generated."""

    def new_paragraph(self, _paragraph_type, _paragraph_level):
        """Assert new paragraph fails."""
        msg = f"Expected {self.expected()}, got new paragraph"
        raise AssertionError(msg)

    def add_run(self, text, _bold, _italic, _pre):
        """Assert text run fails."""
        msg = f'Expected {self.expected()}, got text run "{text}"'
        raise AssertionError(msg)

    def add_hyperlink(self, text, link):
        """Assert link fails."""
        msg = f'Expected {self.expected()}, got link "{text}" <{link}>'
        raise AssertionError(msg)

    def end(self):
        """Assert end fails."""
        msg = f"Expected {self.expected()}, got end"
        raise AssertionError(msg)

    @abstractmethod
    def expected(self):
        """Get a string for the expected thing generated."""


class ChecksEnd(Checks):
    """Tester for an end."""

    def expected(self):
        """Return name."""
        return "end"

    def end(self):
        """Return OK."""


class ChecksText(Checks):
    """Tester for text run."""

    def __init__(self, text, bold, italic, pre):
        """Initialize the text and formatting we expect."""
        super().__init__()
        self.text = text
        self.bold = bold
        self.italic = italic
        self.pre = pre

    def expected(self):
        """Return name."""
        return f'text run "{self.text}"'

    def add_run(self, text, bold, italic, pre):
        """Assert that text and formatting match."""
        assert text == self.text, f'Expected text run "{self.text}", got "{text}"'
        assert bold == self.bold, f'Expected text "{text}" to have boldness {bold}'
        assert (
            italic == self.italic
        ), f'Expected text "{text}" to have italicness {italic}'
        assert pre == self.pre, f'Expected text "{text}" to have monospacedness {pre}'


class ChecksLink(Checks):
    """Tester for link."""

    def __init__(self, text, link):
        """Initialize the text and link we expect."""
        super().__init__()
        self.text = text
        self.link = link

    def expected(self):
        """Return name."""
        return f'hyperlink "{self.text}" <{self.link}>'

    def add_hyperlink(self, text, link):
        """Assert that text and link match."""
        assert (
            text == self.text
        ), f'Expected hyperlink with text "{self.text}", got "{text}"'
        assert (
            link == self.link
        ), f'Expected hyperlink with target "{self.link}", got "{link}"'


class ChecksParagraph(Checks):
    """Tester for new paragraph."""

    def __init__(
        self,
        paragraph_type: DocumentBuilder.ParagraphType = None,
        paragraph_level: int = 0,
    ):
        """Initialize the type and level we expect."""
        super().__init__()
        self.paragraph_type = paragraph_type
        self.paragraph_level = paragraph_level

    def expected(self):
        """Return name."""
        return "new paragraph"

    def new_paragraph(
        self,
        paragraph_type: DocumentBuilder.ParagraphType = None,
        paragraph_level: int = 0,
    ):
        """Assert that type and level match."""
        assert (
            paragraph_type == self.paragraph_type
        ), f"Expected new paragraph to have type {self.paragraph_type}, got {paragraph_type}"
        assert (
            paragraph_level == self.paragraph_level
        ), f"Expected new paragraph to have level {self.paragraph_level}, got {paragraph_level}"
