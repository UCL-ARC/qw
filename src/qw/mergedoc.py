""" Merges data into output documents """
import docx
import lxml
import re

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


class TextSupplier:
    def __init__(self):
        pass
    def set_plain_text(self, run, field_name : str):
        print("replacing", field_name, "in", run)
        run.text = "replacement for {0}!".format(field_name)
    def set_rich_text(self, paragraph, field_name : str):
        print("paragraph for", field_name)
        paragraph.clear()
        paragraph.add_run("Here is some ")
        paragraph.add_run("replacement").italic = True
        paragraph.add_run(" text for " + field_name + "!").bold = True


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
                print(self.field_name)
            return
        if is_fld_end(run):
            print("end", self.field_name, self.text_run)
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
