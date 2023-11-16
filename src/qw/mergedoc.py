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

    The basic format is a dictionary of object names to either
    a dictionary of strings to values, or a list of dictionaries
    of strings to values.

    So you might have:
    {"ObjectName": {
        "id": 45,
        "name": "MyObject",
        "description": "The object that is mine"
    }}
    which would provide three values called "ObjectName.id",
    "ObjectName.name" and "ObjectName.description".

    On the other hand, you could also have:
    {"ObjectName": [{
        "id": 45,
        "name": "MyObject",
        "description": "The object that is mine"
    }, {
        "id": 46,
        "name": "YourObject",
        "description": "The object that is yours"
    }, {
        "id": 47,
        "name": "TheirObject",
        "description": "The object that is theirs"
    }]}
    This also provides the same three values, but there are now
    three of each.

    If you put one or more of these in a paragraph in your template
    document, this paragraph (plus, if it is a heading then all the
    paragraphs beneath it including subheadings) will be copied
    enough times to hold each value.

    Some of these objects might refer to each other. So, if an
    object "MyObject" has a value "OtherObjectName": "123" and there
    is an object called "OtherObjectName", the value is assumed to
    refer to the "OtherObjectName" objects whose "id" key is "123".

    We can use this for nested loops. In this case if you have a
    section of the document with fields from "OtherObjectName" with
    "id": "123" then the fields referring to "MyObject" will only
    select those "MyObject" objects whose "OtherObjectName" values
    match "123".

    In this way we can have a heading advertising "OtherObjectName"
    and then subheadings advertising "MyObject" and each MyObject
    subheading will be placed nicely under the correct
    "OtherObjectName" heading.

    This will also work with nested lists. It will eventually work
    with tables, too, but that might be harder to describe and
    harder to implement.
    """

    def __init__(self, data : Dict[str, Dict[str, Any] | List[Dict[str, Any]]]):
        """
        Initializes with data in the form:

        [{"ObjectNames": [{"key"; "value"}]},
        "ObjectName": {"key", "value"}}]
        """
        logger.debug("Data: {0}", data)
        self.data = data
        # Data that deeper sections will get.
        # For now, it's just the same stuff, but as we start
        # iterations we will narrow this down to only the relevant
        # objects.
        self.deeper = copy.copy(data)
        # Iterations we are currently engaged in at this level.
        self.iterations = dict()

    def get_data(self, field_name : str) -> str:
        """
        Get the named data.

        field_name -- of the form "<object-name>.<key>"
        Return value is a pair (value, is-last). value is None if
        no such field exists (in which case is-last is True). If
        <object-name> has one singular object, is-last will be True.

        If <object-name> refers to a list of objects then value will
        return the "current" value. The "current" value starts as the
        one from the first object, then as we move through the copies
        of the section it will choose subsequent objects. When the
        last object is the "current" object is-last will be returned
        True. We can use this to copy the section the correct number
        of times as we go along.
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

        key -- the name of the object we are iterating through.
        i -- the index we want to set the iteration to.
        Sets the deeper data to be those object that refer to
        this current iteraction.
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
                # Yes, so filter them to those that refer to
                # key in the deeper data.
                self.deeper[d_key] = list(filter(
                    lambda d_obj: d_obj.get(key, None) == id,
                    d_objs
                ))

    def deeper_data(self) -> Self:
        """
        Produce the data for a deeper document level.

        This means that for all the iterations we are currently
        involved in, we need to find the objects that refer to
        the iterated objects and narrow them to the iterations'
        current positions.
        """
        logger.debug("iteration state: {0}", self.iterations)
        for k,i in self.iterations.items():
            objs = self.data[k]
            self.deeper[k] = objs[i] if i < len(objs) else None
        return MergeData(self.deeper)

    def next_section(self):
        """
        Move to the data for the next section at this level.

        This means advancing each of our iterations. Having more
        than one iteration active is a weird thing and it isn't
        clear what we should actually do, but let's just stick
        with this.
        """
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
                # Replace the entire first paragraph
                field_name = fs.pop()
                self._replace_section_head(section, data, field_name)
            else:
                # Just replace the fields with plain text
                self._replace_fields_in_section_head(section, data, fs)
            # Now deal with the deeper sections under the (possibly
            # replaced) first paragraph
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
        """
        Replace a paragraph with the field data.

        Also, replace the entire section if there is no data.
        Also, duplicate the section if we are going to have to do
        this again with another bit of field data.
        """
        (replacement, final) = data.get_data(field_name)
        if not final:
            # There's another piece of data with the same field_name,
            # so we'll duplicate this section before we do the
            # replacement.
            section.duplicate()
        if replacement is None:
            # We are going to replace the entire section with "None."
            section.remove_nonfirst_paragraphs()
            replacement = NONE_PARAGRAPH
        # Replace the section head with the text from the data
        replacer = DocSectionParagraphReplacer(section)
        replacer.render_markdown(replacement)

    def _replace_fields_in_section_head(
            self,
            section : DocSection,
            data : MergeData,
            fs : set[str]
    ):
        """
        Replace the fields in the section's first paragraph.
        
        section -- the section whose head we are replacing.
        data -- the data to pull from.
        fs -- set of field names to replace.
        """
        duplicated = False
        for field_name in fs:
            (replacement_md, final) = data.get_data(field_name)
            if not duplicated and not final:
                # Duplicate this section if we need it for one of these
                # fields and we haven't already done it
                section.duplicate()
                duplicated = True
            if replacement_md is None:
                # One of our fields is exhausted, so we'll replace the
                # entire section. This is probably not very sensible,
                # but it will do for now.
                section.remove_nonfirst_paragraphs()
                replacer = DocSectionParagraphReplacer(section)
                replacer.render_markdown(NONE_PARAGRAPH)
                return
            replacement = markdown_to_plain_text(replacement_md)
            section.replace_field(field_name, replacement)

    def write(self, outputFile : str, data : dict[str, list[str]]) -> None:
        """
        Write out a document based on the template.

        outputFile -- the filename to write to.
        data -- the data to place into the fields.
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
    """
    Load a template MS Word document.
    """
    return Document(templateFile)
