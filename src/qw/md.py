"""Prototyping of extracting structured information from markdown."""
import re

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
