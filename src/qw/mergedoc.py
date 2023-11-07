""" Merges data into output documents """
from abc import ABC, abstractmethod
import docx
from loguru import logger
from lxml.etree import QName
from pathlib import Path
import re

from md import markdown_to_plain_text
from docsection import DocSection, DocSectionParagraphReplacer


class Document:
    def __init__(self, templateFile : str) -> None:
        self.docx = docx.Document(templateFile)
        self.top = DocSection(self.docx)

    def interpolate_sections(self, section : DocSection):
        while section.next():
            fs = section.fields()
            if len(fs) == 1 and section.paragraph_is_only_field():
                field_name = fs.pop()
                if field_name in self.simple:
                    replacer = DocSectionParagraphReplacer(section)
                    replacement = self.simple[field_name]
                    replacer.render_markdown(replacement)
            else:
                for field_name in fs:
                    if field_name in self.simple:
                        replacement = markdown_to_plain_text(self.simple[field_name])
                        section.replace_field(field_name, replacement)
            deeper = section.deeper()
            if deeper:
                self.interpolate_sections(deeper)

    def write(self, outputFile : str, simple : dict[str, str]={}, tables : list[list[dict[str, str]]]=[]) -> None:
        """
        Write out a document based on the template.
        
        outputFile is the filename to write to.
        simple is a dict whose keys are the names of fields to
        replace and whose values are the text to place into
        these fields.
        tables is an array, each element of which is data to put
        into the rows of a table. This table data is an array
        representing the rows of that table, and the rows are
        represented by a dict of names of fields to replace to
        the text to replace with.
        """
        self.simple = simple
        self.interpolate_sections(self.top)
        self.docx.save(outputFile)

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

def load_template(templateFile : str) -> Document:
    return Document(templateFile)
