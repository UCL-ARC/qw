""" Merges data into output documents """
import docx
import re

from md import DocumentBuilder
from lxml.etree import Element, QName

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
        self.paragraph = self.initial_paragraph.insert_paragraph_before(style=None)

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
        pass
    def set_plain_text(self, run, field_name : str):
        PlainTextDocxBuilder(run).render_markdown("Here is **some** markdown _for_ `you`.\n\n* bullet\n1. second bullet")
    def set_rich_text(self, paragraph, field_name : str):
        DocxBuilder(paragraph).render_markdown("Here is **some** markdown _for_ `you`.\n\n* bullet\n1. second bullet")
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
    def parse(self, paragraph):
        ##TODO: also do hyperlinks
        for r in paragraph.runs:
            self.parse_run(r)
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
        supplier = TextSupplier()
        ##TODO: also do tables
        for p in self.doc.paragraphs:
            with FieldParser(supplier) as fp:
                fp.parse(p)
        self.doc.save(outputFile)
    def close(self):
        pass
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()

def load_template(templateFile : str) -> Document:
    return Document(templateFile)
