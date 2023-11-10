""" Merges data into output documents """
from collections.abc import Iterable
import copy
import docx
from loguru import logger
from typing import Self, List, Dict, Any

from md import markdown_to_plain_text
from docsection import DocSection, DocSectionParagraphReplacer

NONE_PARAGRAPH = "*None.*"

class MergeData:
    """
    Data to be merged into the document.
    """
    def __init__(self, data : Dict[str, Dict[str, Any] | List[Dict[str, Any]]]):
        logger.debug("Data: {0}", data)
        self.data = data
        self.iterations = dict()
        self.deeper = copy.copy(data)

    def get_data(self, field_name : str) -> str:
        """
        Returns (value, value is last in list)
        """
        parts = field_name.split(".")
        if len(parts) != 2:
            return (None, True)
        [k, prop] = parts
        logger.debug("Getting {0} . {1}", k, prop)
        if k not in self.data:
            logger.debug("did not find object {0}", k)
            return (None, True)
        obj = self.data[k]
        if obj is None:
            logger.debug("object {0} is None", k)
            return (None, True)
        if type(obj) is dict:
            logger.debug("{0} . {1} is {2} in {3}", k, prop, obj.get(prop, "not present"), obj)
            return (obj.get(prop, None), True)
        if k not in self.iterations:
            logger.debug("beginning iteration for {0}", k)
            self._set_deeper(k, 0)
        index = self.iterations[k]
        if len(obj) <= index:
            logger.debug("iteration {0} is too big an index for {1}", index, obj)
            return (None, True)
        return (obj[index].get(prop, None), index + 1 == len(obj))

    def _set_deeper(self, key, i):
        """
        Work out any dependent objects.
        """
        self.iterations[key] = i
        logger.debug("iteration for {0} is now {1}", key, i)
        objs = self.data[key]
        if objs is None or len(objs) <= i:
            return
        obj = objs[i]
        if type(obj) is not dict:
            return
        id = obj.get('id', None)
        if id is None:
            return
        # Find out which other values in self.data
        # are refer to obj
        for d_key, d_objs in self.data.items():
            # do the d_objs refer back to `key`?
            if (
                type(d_objs) is list
                and len(d_objs) != 0
                and key in d_objs[0]
            ):
                self.deeper[d_key] = list(filter(
                    lambda d_obj: d_obj.get(key, None) == id,
                    d_objs
                ))

    def deeper_data(self) -> Self:
        logger.debug("iteration state: {0}", self.iterations)
        for k,i in self.iterations.items():
            objs = self.data[k]
            self.deeper[k] = objs[i] if i < len(objs) else None
        return MergeData(self.deeper)

    def next_section(self):
        for k, i in self.iterations.items():
            self._set_deeper(k, i + 1)


class Document:
    def __init__(self, templateFile : str) -> None:
        self.docx = docx.Document(templateFile)
        self.top = DocSection(self.docx)

    def interpolate_sections(self, section : DocSection, data: MergeData):
        logger.debug("Starting section")
        while section.next():
            fs = section.fields()
            if len(fs) == 1 and section.paragraph_is_only_field():
                field_name = fs.pop()
                self._replace_section_head(section, data, field_name)
            else:
                self._replace_fields_in_section_head(section, data, fs)
            deeper = section.deeper()
            if deeper:
                self.interpolate_sections(deeper, data.deeper_data())
            data.next_section()
        logger.debug("Finished section")

    def _replace_section_head(
        self,
        section : DocSection,
        data : MergeData,
        field_name : str
    ):
        (replacement, final) = data.get_data(field_name)
        logger.debug("Data for {0}: {1} (final: {2})", field_name, replacement, final)
        if not final:
            section.duplicate()
        if replacement is None:
            section.remove_nonhead_paragraphs()
            replacement = NONE_PARAGRAPH
        replacer = DocSectionParagraphReplacer(section)
        replacer.render_markdown(replacement)

    def _replace_fields_in_section_head(
            self,
            section : DocSection,
            data : MergeData,
            fs : set[str]
    ):
        duplicated = False
        for field_name in fs:
            (replacement_md, final) = data.get_data(field_name)
            logger.debug("Data for field {0}: {1} (final: {2})", field_name, replacement_md, final)
            if not duplicated and not final:
                section.duplicate()
                duplicated = True
            if replacement_md is None:
                section.remove_nonhead_paragraphs()
                replacer = DocSectionParagraphReplacer(section)
                replacer.render_markdown(NONE_PARAGRAPH)
                return
            replacement = markdown_to_plain_text(replacement_md)
            section.replace_field(field_name, replacement)

    def write(self, outputFile : str, data : dict[str, list[str]]) -> None:
        """
        Write out a document based on the template.
        
        outputFile is the filename to write to.
        """
        self.interpolate_sections(self.top, MergeData(data))
        self.docx.save(outputFile)

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

def load_template(templateFile : str) -> Document:
    return Document(templateFile)
