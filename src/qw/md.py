"""Prototyping of extracting structured information from markdown."""
from pathlib import Path

from markdown import markdown
from parsel import Selector


def text_under_heading(file: Path, heading: str) -> str:
    """Extract text elements under a specific heading."""
    text = file.read_text()
    html = markdown(text)
    selector = Selector(html)
    header = selector.xpath('//h3[contains(text(), "What happened?")]')
    if not header:
        msg = f"Header '{heading}' not found"
        RuntimeError(msg)

    return header.xpath("following-sibling::p/text()").get().strip()
