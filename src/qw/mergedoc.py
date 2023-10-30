""" Merges data into output documents """
import copy
import docx
from loguru import logger
from lxml.etree import QName
from pathlib import Path
import re

from md import DocumentBuilder, text_under_heading

def first_key(ds : list[dict]):
    for d in ds:
        for k in d.keys():
            return k
    return None

mergefield_re = re.compile(r"\s*MERGEFIELD\s+(.*?)\s*")


def is_fld_begin(run):
    return 0 < len(run.element.xpath('w:fldChar[@w:fldCharType="begin"]'))


def is_fld_end(run):
    return 0 < len(run.element.xpath('w:fldChar[@w:fldCharType="end"]'))


def is_text(run):
    return 0 < len(run.element.xpath('w:t'))


def instr_elt(run):
    instrTexts = run.element.xpath('w:instrText')
    if len(instrTexts) == 0:
        return None
    return instrTexts[0]


class DocxBuilder(DocumentBuilder):

    def __init__(self, paragraph):
        self.initial_paragraph = paragraph


    def new_paragraph(
        self,
        paragraph_type : DocumentBuilder.ParagraphType=None,
        paragraph_level : int=0
    ):
        self.paragraph = self.initial_paragraph.insert_paragraph_before(
            style=None
        )

        num_id = None
        if paragraph_type == DocumentBuilder.ParagraphType.LIST_UNORDERED:
            num_id = 1
        elif paragraph_type == DocumentBuilder.ParagraphType.LIST_ORDERED:
            num_id = 2
        if num_id is not None:
            nsmap = docx.oxml.ns.nsmap
            elt = self.paragraph._p
            pPr = elt.makeelement(QName(nsmap['w'], 'pPr'))
            numPr = elt.makeelement(QName(nsmap['w'], 'numPr'))
            pPr.append(numPr)
            numPr.append(
                elt.makeelement(
                    QName(nsmap['w'], 'ilvl'),
                    attrib={ QName(nsmap['w'], 'val'): str(paragraph_level) }
                )
            )
            numPr.append(
                elt.makeelement(
                    QName(nsmap['w'], 'numId'),
                    attrib={ QName(nsmap['w'], 'val'): str(num_id) }
                )
            )
            self.paragraph._p.append(pPr)


    def add_run(self, text : str, bold : bool=None, italic : bool=None, pre : bool=None):
        run = self.paragraph.add_run(text)
        run.bold = bold
        run.italic = italic
        if pre:
            run.font.name = 'Courier'


    def add_hyperlink(self, text : str, link : str, bold : bool=None, italic : bool=None, pre : bool=None):
        run = self.paragraph.add_run("Link {0}: {1}".format(text, link))


class PlainTextDocxBuilder(DocumentBuilder):

    def __init__(self, run):
        self.run = run
        self.fresh = True


    def new_paragraph(
        self,
        paragraph_type : DocumentBuilder.ParagraphType=None,
        paragraph_level : int=0
    ):
        if self.fresh:
            self.fresh = False
            self.run.text = ''
        else:
            self.run.add_break()


    def add_run(self, text : str, bold : bool=None, italic : bool=None, pre : bool=None):
        self.run.text = self.run.text + text


    def add_hyperlink(self, text : str, link : str, bold : bool=None, italic : bool=None, pre : bool=None):
        self.run.text = self.run.text + "Link {0}: {1}".format(text, link)


class TextSupplier:
    def __init__(self):
        file = Path(__file__).parent.parent.parent / "tests" / "resources" / "markdown" / "test_data.md"
        md = file.read_text()
        self.fields = {
            'software-requirement-id': text_under_heading(md, "ID"),
            'software-requirement-name': text_under_heading(md, "Name"),
            'software-requirement-description': text_under_heading(md, "Description"),
            'system-requirement-id': text_under_heading(md, "System requirements")
        }
    def set_plain_text(self, run, field_name : str):
        value = self.fields.get(field_name)
        if value:
            PlainTextDocxBuilder(run).render_markdown(value)
    def set_rich_text(self, paragraph, field_name : str):
        value = self.fields.get(field_name)
        if value:
            DocxBuilder(paragraph).render_markdown(value)
            paragraph.clear()


class FieldParser:
    def __init__(self, supplier : TextSupplier):
        self.supplier = supplier
        self.paragraph_is_only_field = True
        self.begin = None
        self.field_name = None
        self.text_run = None
    def replace_paragraph(self, paragraph):
        """Replaces the entire paragraph if it is only a single field."""
        if self.paragraph_is_only_field and self.text_run:
            self.supplier.set_rich_text(paragraph, self.field_name)
            self.text_run = None
    def replace_text_run(self):
        if self.text_run:
            self.supplier.set_plain_text(self.text_run, self.field_name)
            self.text_run = None
    def parse_run(self, run):
        if is_fld_begin(run):
            self.replace_text_run()
            self.begin = run
            return
        if self.begin is None:
            self.paragraph_is_only_field = False
            return
        instr = instr_elt(run)
        if instr is not None:
            mergefield_result = mergefield_re.fullmatch(instr.text)
            if mergefield_result:
                self.field_name = mergefield_result.group(1)
            return
        if is_fld_end(run):
            self.begin = None
            return
        if self.text_run is None and is_text(run):
            self.text_run = run
    def parse_hyperlink(self, hyperlink):
        """
        Hyperlinks do not have fields in them.
        """
        self.paragraph_is_only_field = False
    def parse(self, paragraph):
        for bit in paragraph.iter_inner_content():
            if isinstance(bit, docx.text.paragraph.Run):
                self.parse_run(bit)
            elif isinstance(bit, docx.text.paragraph.Hyperlink):
                self.parse_hyperlink(bit)
            else:
                logger.warning(
                    'Internal error: Part of a paragraph that is'
                    ' neither a Run nor a Hyperlink'
                )
        self.replace_paragraph(paragraph)
    def close(self):
        self.replace_text_run()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()


class Document:
    def __init__(self, templateFile : str) -> None:
        self.doc = docx.Document(templateFile)
        self.supplier = TextSupplier()
    def interpolate_paragraph(self, paragraph):
        with FieldParser(self.supplier) as fp:
            fp.parse(paragraph)
    def interpolate_table(self, table):
        for row in table.rows:
            for cell in row.cells:
                # tables-in-tables is a bit tricky with this API
                for p in cell.paragraphs:
                    self.interpolate_paragraph(p)
    def interpolate_section(self, section):
        if isinstance(section, docx.text.paragraph.Paragraph):
            self.interpolate_paragraph(section)
        elif isinstance(section, docx.table.Table):
            self.interpolate_table(section)
        elif isinstance(section, docx.section.Section):
            for subsection in section.iter_inner_content():
                self.interpolate_section(subsection)
        else:
            logger.warning(
                'Was not expecting subsection type {0}'. format(
                    type(section)
                )
            )
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
        for section in self.doc.sections:
            self.interpolate_section(section)
        self.doc.save(outputFile)
    def close(self):
        pass
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()

def load_template(templateFile : str) -> Document:
    return Document(templateFile)
