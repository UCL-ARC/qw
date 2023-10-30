"""Prototyping of extracting structured information from markdown."""
import re
from abc import ABC, abstractmethod
from enum import Enum
import itertools

from qw.base import QwError


def text_under_heading(text: str, heading: str) -> str:
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
        msg = f"Could not find the heading: '### {heading}'"
        raise QwError(msg)

    return "\n".join(sub_heading_lines).strip()


# Breaking Markdown text into paragraphs of some type
FENCED_RE = re.compile(r"(?:^|\n+)(?:~{3,}|`{3,})\s*(.*?)\n([\S\s]*?)\n(?:~{3,}|`{3,})(?:$|\n+)")
PARAGRAPH_RE = re.compile(r"\n{2,}|\n(?=\s*[\*\+\-]\s)")

# Determinig the type of a paragraph
## - item
LISTU_RE = re.compile(r"(\s*)[\*\+\-]\s+(.*)")
## 1. item
LISTO_RE = re.compile(r"(\s*)\d+\.\s+(.*)")

# Breaking Markdown paragraphs into runs of some type
## **bold**
ASTERISK2_RE = re.compile(r"\*\*(\S(?:.*\S)?)\*\*(?=[^*])")
## __bold__
UNDERSCORE2_RE = re.compile(r"(?:^|(?<=\s))__(\S(?:.*\S)?)__(?:$|(?=\s))")
## *italic*
ASTERISK1_RE = re.compile(r"\*(\S(?:.*\S)?)\*")
## _italic_
UNDERSCORE1_RE = re.compile(r"(?:^|(?<=\s))_(\S(?:.*\S)?)_(?:$|(?=\s))")
## `preformated`
BACKTICK_RE = re.compile(r"`([^` \t\r\n].*?)`")
## [[link]]
SQUARE2_RE = re.compile(r"\[\[(.+?)\]\](?=[^\]])")
## [text](link)
LINK_RE = re.compile(r"\[(.+?)\]\((.+?)\)")


class DocumentBuilder(ABC):
    class ParagraphType(Enum):
        PREFORMATTED = 10
        LIST_ORDERED = 11
        LIST_UNORDERED = 12

    @abstractmethod
    def new_paragraph(
        self,
        paragraph_type : ParagraphType=None,
        paragraph_level : int=0
    ):
        pass


    @abstractmethod
    def add_run(self, text : str, bold : bool=None, italic : bool=None, pre : bool=None):
        pass


    @abstractmethod
    def add_hyperlink(self, text : str, link : str, bold : bool=None, italic : bool=None, pre : bool=None):
        pass


    def render_markdown_not_pre(self, text : str, link : str, bold : bool, italic : bool):
        if not text:
            return
        linx = SQUARE2_RE.split(text)
        for i in range(0, len(linx), 2):
            run = linx[i]
            if run:
                linx2 = LINK_RE.split(run)
                for j in range(0, len(linx2), 3):
                    self.add_run(linx2[j], bold=bold, italic=italic)
                    if j + 2 < len(linx2):
                        self.add_hyperlink(linx2[j + 1], linx2[j + 2], bold=bold, italic=italic)
            if i + 1 < len(linx):
                self.add_hyperlink(linx[i + 1], link[i + 1], bold=bold, italic=italic)


    def render_markdown_bold_italic_run(self, text : str, bold : bool, italic : bool):
        if not text:
            return
        backtix = BACKTICK_RE.split(text)
        for i in range(0, len(backtix), 2):
            self.add_run(backtix[i], bold=bold, italic=italic, pre=None)
            if i + 1 < len(backtix):
                self.add_run(backtix[i + 1], bold=bold, italic=italic, pre=True)


    def render_markdown_bold_run(self, text : str, bold : bool):
        if not text:
            return
        italix = ASTERISK1_RE.split(text)
        for i in range(0, len(italix), 2):
            upright_run = italix[i]
            if upright_run:
                italix2 = UNDERSCORE1_RE.split(upright_run)
                for j in range(0, len(italix2), 2):
                    self.render_markdown_bold_italic_run(italix2[j], bold=bold, italic=None)
                    if j + 1 < len(italix2):
                        self.render_markdown_bold_italic_run(italix2[j + 1], bold=bold, italic=True)
            if i + 1 < len(italix):
                self.render_markdown_bold_italic_run(italix[i + 1], bold=bold, italic=True)


    def render_markdown_paragraph(self, text : str):
        bolds = ASTERISK2_RE.split(text)
        for i in range(0, len(bolds), 2):
            unbold_run = bolds[i]
            if unbold_run:
                bolds2 = UNDERSCORE2_RE.split(unbold_run)
                for j in range(0, len(bolds2), 2):
                    self.render_markdown_bold_run(bolds2[j], bold=None)
                    if j + 1 < len(bolds2):
                        self.render_markdown_bold_run(bolds2[j + 1], bold=True)
            if i + 1 < len(bolds):
                self.render_markdown_bold_run(bolds[i + 1], bold=True)


    def render_markdown_paragraphs(self, text : str):
        if not text:
            return
        # Previously seen indent levels still active
        for para in PARAGRAPH_RE.split(text):
            indents = []
            lines_so_far = []
            for line in para.splitlines():
                r = LISTO_RE.fullmatch(line)
                if r:
                    para_type = DocumentBuilder.ParagraphType.LIST_ORDERED
                else:
                    r = LISTU_RE.fullmatch(line)
                    if r:
                        para_type = DocumentBuilder.ParagraphType.LIST_UNORDERED
                if r:
                    # Work out what indent level we are at
                    indent = len(r.group(1))
                    indents = list(
                        itertools.takewhile(lambda x: x < indent, indents)
                    ) + [indent]
                    if lines_so_far:
                        # Output previous (non list) paragraph
                        self.new_paragraph()
                        self.render_markdown_paragraph("\n".join(lines_so_far))
                        lines_so_far = []
                    # Output current list iten
                    self.new_paragraph(para_type, paragraph_level=len(indents) - 1)
                    self.render_markdown_paragraph(r.group(2))
                else:
                    lines_so_far.append(line)
                    indents = []
            if lines_so_far:
                # Output trailing non-list paragraph
                self.new_paragraph()
                self.render_markdown_paragraph("\n".join(lines_so_far))


    def render_markdown(self, text : str):
        fenceds = FENCED_RE.split(text)
        for i in range(0, len(fenceds), 3):
            para = fenceds[i]
            self.render_markdown_paragraphs(para)
            if i + 2 < len(fenceds):
                self.new_paragraph(
                    DocumentBuilder.ParagraphType.PREFORMATTED
                )
                self.add_run(fenceds[i + 2])
