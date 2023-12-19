"""Prototyping of extracting structured information from markdown."""
import re
from abc import ABC, abstractmethod
from enum import Enum

from qw.base import QwError


def text_under_heading(
    text: str, heading: str, default: str | None=None
) -> str:
    """Extract all markdown after a h3 heading, until the next h3 heading."""
    heading_pattern = re.compile(f"^### +{re.escape(heading)}")
    sub_heading_lines = []

    found_heading = False
    for line in text.split("\n"):
        # skip all rows before the header
        if not found_heading:
            if not heading_pattern.match(line):
                continue
            # have now found the header go to next line and stop skipping lines that don't match the header
            found_heading = True
            continue
        if line.startswith("### "):
            # found the next header, exit
            break
        sub_heading_lines.append(line)

    if not found_heading:
        if default is not None:
            return default
        msg = f"Could not find the heading: '### {heading}'"
        raise QwError(msg)

    return "\n".join(sub_heading_lines).strip()


# Breaking Markdown text into paragraphs of some type.
# Picking out fenced code:
FENCED_RE = re.compile(
    r"""
    (?:^|\n+)        # The start of a line
    (?:~{3,}|`{3,})  # At least three backticks or tildes for the first fence
    [ \t]*(.*?)\n    # Capturing the format name after the first fence
    ([\S\s]*?)\n     # Capturing the fenced code: [\S\s] = Anything (including newlines)
    (?:~{3,}|`{3,})  # At least three backticks or tildes for the second fence
    (?:$|\n+)        # The end of a line
    """,
    re.VERBOSE,
)
# Paragraph delimiters. We don't test for numbers at the start of
# lines because numbered lists must be separated from other paragraphs
# by a blank line anyway.
PARAGRAPH_RE = re.compile(
    r"""
    \n{2,}|  # a blank line
    \n(?=\s*[\*\+\-]\s)  # a bullet at the start of the line.
    """,
    re.VERBOSE,
)

# Determinig the type of a paragraph
## - item
LISTU_RE = re.compile(r"(\s*)[\*\+\-]\s+(.*)")
## 1. item
LISTO_RE = re.compile(r"(\s*)\d+\.\s+(.*)")

# Breaking Markdown paragraphs into runs of some type
## **bold**
ASTERISK2_RE = re.compile(
    r"""
    \*\*(\S(?:.*\S)?)\*\*  # ** surrounding (captured) nonspaces surrounding text
    (?=[^*])               # not followed by *, so ***text*** -> bold *text*
    """,
    re.VERBOSE,
)
## __bold__
UNDERSCORE2_RE = re.compile(
    r"""
    (?:^|(?<=\s))      # start of text or previous space
    __(\S(?:.*\S)?)__  # __ surrounding (captured) nonspaces surrounding text
    (?:$|(?=\s))       # end of text or following space
    """,
    re.VERBOSE,
)
## *italic*
ASTERISK1_RE = re.compile(r"\*(\S(?:.*\S)?)\*")
## _italic_
UNDERSCORE1_RE = re.compile(
    r"""
    (?:^|(?<=\s))    # start of text or previous space
    _(\S(?:.*\S)?)_  # _ surrounding (captured) nonspaces surrounding text
    (?:$|(?=\s))     # end of text or following space
    """,
    re.VERBOSE,
)
## `preformated`
BACKTICK_RE = re.compile(r"`([^` \t\r\n].*?)`")
## hyperlink looking like [[link]]
SQUARE2_RE = re.compile(r"\[\[(.+?)\]\](?=[^\]])")
## hyperlink looking like (text)[link]
LINK_RE = re.compile(r"\[(.+?)\]\((.+?)\)")


class DocumentBuilder(ABC):
    """
    Renders Markdown documents in some other format.

    Override the abstract methods to insert text into
    the target document.
    """

    class ParagraphType(Enum):
        """Types of paragraph that Markdown knows about."""

        HEADING = 1
        PREFORMATTED = 2
        LIST_ORDERED = 3
        LIST_UNORDERED = 4

    class Boldness(Enum):
        """Bold or not."""

        UNBOLD = 0
        BOLD = 1

    class Italicness(Enum):
        """Italic or not."""

        UPRIGHT = 0
        ITALIC = 1

    class Spacing(Enum):
        """Monospaced or not."""

        PROPORTIONAL = 0
        MONOSPACED = 1

    @abstractmethod
    def new_paragraph(
        self,
        paragraph_type: ParagraphType | None = None,
        paragraph_level: int = 0,
    ):
        """
        Start a new paragraph at the end of the target document.

        paragraph_type -- Whether the paragraph is a heading,
            preformatted paragraph, bulleted list item or numbered
            list item.
        paragraph_level -- The outline level of the pagagraph for
            headings (0 is most important), or the indent level
            for list items (0 is no indent).
        """

    @abstractmethod
    def add_run(
        self,
        text: str,
        bold: Boldness | None = None,
        italic: Italicness | None = None,
        pre: Spacing | None = None,
    ):
        """
        Add a run of text to the end of the current paragraph.

        text -- The text of the run to add.
        bold -- True if the text should be bold.
        italic -- True if the text should be italic.
        pre -- True if the text should be in a monospaced font.
        """

    @abstractmethod
    def add_hyperlink(
        self,
        text: str,
        link: str,
    ):
        """Add a hyperlink to the end of the current paragraph."""

    @abstractmethod
    def end(self):
        """End parsing."""

    def _render_markdown_not_pre(
        self,
        text: str,
        bold: Boldness | None,
        italic: Italicness | None,
    ):
        if not text:
            return
        # Split the text into non-link/[[link]] runs
        linx = SQUARE2_RE.split(text)
        for i in range(0, len(linx), 2):
            run = linx[i]
            if run:
                # Not a [[link]], but there might be [text](link)s
                linx2 = LINK_RE.split(run)
                # Produces triples (nonlink, link-text, link-target)
                for j in range(0, len(linx2), 3):
                    # Render non-link
                    self.add_run(linx2[j], bold=bold, italic=italic)
                    if j + 2 < len(linx2):
                        # Render the link
                        self.add_hyperlink(
                            linx2[j + 1],
                            linx2[j + 2],
                        )
            if i + 1 < len(linx):
                # Add [[double squares]] type link
                self.add_hyperlink(linx[i + 1], linx[i + 1])

    def _render_markdown_bold_italic_run(
        self,
        text: str,
        bold: Boldness | None,
        italic: Italicness | None,
    ):
        """Render a bold/italic/both/neither run, finding other formatting."""
        if not text:
            return
        # Split the text into non-preformatted/preformatted runs
        backtix = BACKTICK_RE.split(text)
        for i in range(0, len(backtix), 2):
            # Render the non-preformatted run
            self._render_markdown_not_pre(
                backtix[i],
                bold=bold,
                italic=italic,
            )
            if i + 1 < len(backtix):
                # Render the preformatted run
                self.add_run(
                    backtix[i + 1],
                    bold=bold,
                    italic=italic,
                    pre=DocumentBuilder.Spacing.MONOSPACED,
                )

    def _render_markdown_bold_run(
        self,
        text: str,
        bold: Boldness | None,
    ):
        """Render a bold or non-bold run, finding other formatting."""
        if not text:
            return
        # Split the text into non-asterisked-italic/asterisked-italic runs
        italix = ASTERISK1_RE.split(text)
        for i in range(0, len(italix), 2):
            upright_run = italix[i]
            if upright_run:
                # It is not asterisked, but is it underscored?
                italix2 = UNDERSCORE1_RE.split(upright_run)
                for j in range(0, len(italix2), 2):
                    # Neither underscored nor asterisked italic
                    self._render_markdown_bold_italic_run(
                        italix2[j],
                        bold=bold,
                        italic=None,
                    )
                    if j + 1 < len(italix2):
                        # Render underscored-italic run
                        self._render_markdown_bold_italic_run(
                            italix2[j + 1],
                            bold=bold,
                            italic=DocumentBuilder.Italicness.ITALIC,
                        )
            if i + 1 < len(italix):
                # render the asterisked-italic run
                self._render_markdown_bold_italic_run(
                    italix[i + 1],
                    bold=bold,
                    italic=DocumentBuilder.Italicness.ITALIC,
                )

    def _render_markdown_paragraph(self, text: str):
        """Render one paragraph (after it has been started)."""
        # Split the text into non-asterisked-bold/asterisked-bold runs
        bolds = ASTERISK2_RE.split(text)
        for i in range(0, len(bolds), 2):
            unbold_run = bolds[i]
            if unbold_run:
                # Not asterisked-bold, so find __underscored__ bold
                bolds2 = UNDERSCORE2_RE.split(unbold_run)
                for j in range(0, len(bolds2), 2):
                    # Neither asterisked nor underscored bold
                    self._render_markdown_bold_run(bolds2[j], bold=None)
                    if j + 1 < len(bolds2):
                        # Underscored bold
                        self._render_markdown_bold_run(
                            bolds2[j + 1],
                            bold=DocumentBuilder.Boldness.BOLD,
                        )
            if i + 1 < len(bolds):
                # Render the asterisked-bold run
                self._render_markdown_bold_run(
                    bolds[i + 1],
                    bold=DocumentBuilder.Boldness.BOLD,
                )

    def _render_markdown_paragraphs(self, text: str):
        """Render consecutive non-fenced paragraphs."""
        if not text:
            return
        # We need to know how many indents we have seen so far that
        # are still active, and how big those indents were. We need
        # this so that when we see an indent of n spaces we know
        # which indent that actually is. Any deeper indents are then
        # no longer active. `indents` is a list of integers; the
        # numbers of spaces that represent each indent.
        indents: list[int] = []
        # Split into paragraphs, which are delimited by multiple
        # newlines or start with *, -, + or a dotted number.
        for para in PARAGRAPH_RE.split(text):
            # Gathered lines for non-list-item paragraphs
            lines_so_far: list[str] = []
            for line in para.splitlines():
                # Numbered list item?
                re_res = LISTO_RE.fullmatch(line)
                if re_res is not None:
                    para_type = DocumentBuilder.ParagraphType.LIST_ORDERED
                else:
                    # Bullet list item?
                    re_res = LISTU_RE.fullmatch(line)
                    if re_res is not None:
                        para_type = DocumentBuilder.ParagraphType.LIST_UNORDERED
                # it is a list item
                if re_res is not None:
                    # Work out what indent level we are at
                    indent = len(re_res.group(1))
                    # Which previously seen indents are still active?
                    indents = indents[: _count_prefix_less_than(indent, indents)]
                    # And add the new one.
                    indents.append(indent)
                    if lines_so_far:
                        # Output previous (non list item) paragraph
                        self.new_paragraph()
                        self._render_markdown_paragraph("\n".join(lines_so_far))
                        lines_so_far = []
                    # Output current list iten
                    self.new_paragraph(para_type, paragraph_level=len(indents) - 1)
                    self._render_markdown_paragraph(re_res.group(2))
                else:
                    lines_so_far.append(line)
                    indents = []
            if lines_so_far:
                # Output trailing non-list paragraph
                self.new_paragraph()
                self._render_markdown_paragraph("\n".join(lines_so_far))

    def render_markdown(self, text: str):
        """
        Render markdown into the target document.

        text -- markdown formatted string to render.
        """
        # This first stage splits the text into runs of unfenced
        # paragraphs and runs of fenced paragraphs. The output of
        # this regular expression are triples (unfenced-text,
        # fenced-specification, fenced-text) repeating then with
        # one final unfenced-text at the end. Currently we do
        # nothing with the fenced-specification.
        fenceds = FENCED_RE.split(text)
        for i in range(0, len(fenceds), 3):
            para = fenceds[i]
            # Render the unfenced text, needs further parsing.
            self._render_markdown_paragraphs(para)
            if i + 2 < len(fenceds):
                # We don't need to look for any more markdown
                # within fenced text so we just render it.
                self.new_paragraph(DocumentBuilder.ParagraphType.PREFORMATTED)
                self.add_run(fenceds[i + 2])
        self.end()


def _count_prefix_less_than(num, es):
    """Count how long a prefix of es has elements less than num."""
    n = 0
    for e in es:
        if num <= e:
            return n
        n += 1
    return n


class PlainTextBuilder(DocumentBuilder):
    """
    DocumentBuilder for building plain text.

    This effectively removes all formatting from a markdown string.
    Usage:
        ptb = PlainTextBuilder()
        ptb.render_markdown(markdown_text)
        plain_text = ptb.out
    """

    def __init__(self):
        """Initialize an empty object."""
        self.out = ""
        self.first = True

    def new_paragraph(self, *_args, **_kwargs):
        """DocumentBuilder override."""
        if self.first:
            self.first = False
        else:
            self.out += "\n"

    def add_run(self, text: str, *_args, **_kwargs):
        """DocumentBuilder override."""
        self.out += text

    def add_hyperlink(self, text: str, link: str):
        """DocumentBuilder override."""
        self.out += f"{text} <{link}>"

    def end(self):
        """DocumentBuilder override."""


def markdown_to_plain_text(markdown: str) -> str:
    r"""
    Remove the formatting from markdown.

    Turns the markdown into a plain text string. Paragraphs
    are delimited by \n. Hyperlinks are rendered as
    "text <link>".
    """
    builder = PlainTextBuilder()
    builder.render_markdown(markdown)
    return builder.out
