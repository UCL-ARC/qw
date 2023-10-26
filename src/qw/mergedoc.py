""" Merges data into output documents """
from mailmerge import MailMerge
import locale

def first_key(ds : list[dict]):
    for d in ds:
        for k in d.keys():
            return k
    return None

class Document:
    def __init__(self, templateFile : str) -> None:
        self.doc = MailMerge(templateFile)
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
        locale.setlocale(locale.LC_TIME, '')
        for table in tables:
            k = first_key(table)
            if k is not None:
                self.doc.merge_rows(k, table)
        self.doc.merge(**simple)
        self.doc.write(outputFile)
    def close(self):
        self.doc.close()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()

def load_template(templateFile : str) -> Document:
    return Document(templateFile)
