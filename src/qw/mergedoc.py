"""Merges data into output documents."""
import copy
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeAlias

import docx
from loguru import logger

from qw.docsection import DocSection, DocSectionParagraphReplacer
from qw.md import markdown_to_plain_text

NONE_PARAGRAPH = "*None.*"

_MergeData: TypeAlias = "MergeData"


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

    Some of these objects might refer to each other. The argument
    filter_referencers is a function taking arguments
    (from_obj_type, from_objs, to_obj_type, to_obj).
    from_obj_type is a key from data and from_objs are the
    associated values. to_obj_type is a different key from data
    and to_obj is one of the associated values. The function
    should return those elements of from_objs that refer to
    to_obj. If the from_obj_type objects never refer to
    to_obj_type objects, None should be returned.

    We can use this for nested loops. If filter_referencers returns
    a subset, these will be the only ones of those objects
    available to the paragraphs under this one.

    This works for headings with paragraphs underneath, and for
    lists with sublists underneath.
    """

    # Type of a function that filters objects to be only those
    # that point to another object
    FilterReferencesCallable: TypeAlias = Callable[
        [
            str,  # from_obj_type
            list[dict[str, Any]],  # from_objs
            str,  # to_obj_type
            dict[str, Any],  # to_obj
        ],
        list[dict[str, Any]],
    ]

    def __init__(
        self,
        data: dict[str, Any],
        filter_referencers: FilterReferencesCallable,
    ):
        """
        Initialize with data.

        Data must be in the form:

        [{"ObjectNames": [{"key"; "value"}]},
        "ObjectName": {"key", "value"}}]

        The filter_referencers callable takes arguments:

        filter_referencers(from_obj_type, from_obj, to_obj_type, to_obj)

        For example:

        filter_referencers(
            "software-requirement",
            [
                {"id":5, "user-need": 1, ... },
                {"id":6, "user-need": 2, ... },
                {"id":7, "user-need": 2, ... },
                {"id":8, "user-need": 3, ... },
            ]
            "user-need",
            {"id": 2, ... }
        )

        and in this case should return:

        [
            {"id":6, "user-need": 2, ... },
            {"id":7, "user-need": 2, ... },
        ]

        because these are the elements of from_obj that refer to the
        to_obj argument.
        """
        logger.debug("Data: {0}", data)
        self.data = data
        # Data that deeper sections will get.
        # For now, it's just the same stuff, but as we start
        # iterations we will narrow this down to only the relevant
        # objects.
        self.deeper = copy.copy(data)
        # Iterations we are currently engaged in at this level.
        self.iterations: dict[str, int] = {}
        self.filter_referencers = filter_referencers
        self.iteration_advance: set[str] = set()

    def get_data(self, field_name: str) -> tuple[str | None, bool]:
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
        try:
            [k, prop] = parts
        except ValueError:
            return (None, True)
        logger.debug("Getting {0} . {1}", k, prop)
        if k not in self.data:
            logger.debug("did not find object {0}", k)
            return (None, True)
        obj = self.data[k]
        if obj is None:
            logger.debug("object {0} is None", k)
            return (None, True)
        if isinstance(obj, dict):
            logger.debug(
                "{0} . {1} is {2} in {3}",
                k,
                prop,
                obj.get(prop, "not present"),
                obj,
            )
            return (obj.get(prop, None), True)
        self.iteration_advance.add(k)
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
        objs = self.data[key]
        if objs is None or len(objs) <= i:
            logger.debug("no more objects")
            return
        obj = objs[i]
        if not isinstance(obj, dict):
            logger.debug("not a real object")
            return
        # Find out which other values in self.data
        # refer to obj
        for d_key, d_objs in self.data.items():
            if isinstance(d_objs, list) and len(d_objs) != 0:
                # do the d_objs refer to `key`?
                refs = self.filter_referencers(d_key, d_objs, key, obj)
                if refs is not None:
                    logger.debug("Filtered {} by reference to {}", d_key, obj)
                    self.deeper[d_key] = list(refs)

    def deeper_data(self) -> _MergeData:
        """
        Produce the data for a deeper document level.

        This means that for all the iterations we are currently
        involved in, we need to find the objects that refer to
        the iterated objects and narrow them to the iterations'
        current positions.
        """
        logger.debug("deeper: iteration state: {0}", self.iterations)
        for k, objs in self.data.items():
            i = self.iterations.get(k, None)
            if i is not None:
                self.deeper[k] = objs[i] if i < len(objs) else None
        return MergeData(self.deeper, self.filter_referencers)

    def reset_iterations(self):
        """Reset the iterations for all the data."""
        for k in self.iterations:
            self._set_deeper(k, 0)

    def next_section(self):
        """
        Move to the data for the next section at this level.

        This means advancing each of our iterations. Having more
        than one iteration active is a weird thing and it isn't
        clear what we should actually do, but let's just stick
        with this.
        """
        logger.debug("next: iteration state: {0}", self.iterations)
        for k, i in self.iterations.items():
            increment = 1 if k in self.iteration_advance else 0
            self._set_deeper(k, i + increment)
        self.iteration_advance.clear()


class Document:
    """MS Word document with MergeFields to be replaced."""

    def __init__(self, template_file: str) -> None:
        """Initialize the document from a template file."""
        self.docx = docx.Document(template_file)
        self.top = DocSection(self.docx)

    def _interpolate_sections(self, section: DocSection, data: MergeData):
        """
        Interpolate Mergefields.

        section -- interpolate the mergefields iterated through by this
        data -- the data to merge into these mergefields.
        """
        logger.debug("Starting section")
        while section.next_section():
            logger.debug(f"section {section.start_index}-{section.end_index}")
            fs = section.fields()
            if len(fs) == 1 and section.paragraph_is_only_field():
                # Replace the entire section
                for field_name in fs:
                    # there is only one of these (so only one iteration)
                    self._replace_section_head(section, data, field_name)
            else:
                # Just replace the fields with plain text
                self._replace_fields_in_section_head(section, data, fs)
                # Now deal with the deeper sections under the (possibly
                # replaced) first paragraph
                deeper = section.deeper()
                if deeper:
                    self._interpolate_sections(deeper, data.deeper_data())
            if section.at_iteration_end():
                logger.debug(f"Resetting iterations, depth: {section._depth()}")
                data.reset_iterations()
            else:
                data.next_section()
        logger.debug("Finished section")

    def _replace_section_head(
        self,
        section: DocSection,
        data: MergeData,
        field_name: str,
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
        section: DocSection,
        data: MergeData,
        fs: set[str],
    ):
        """
        Replace the fields in the section's first paragraph.

        section -- the section whose head we are replacing.
        data -- the data to pull from.
        fs -- set of field names to replace.
        """
        if len(fs) == 0:
            return
        duplicated = False
        replaced_any = False
        for field_name in fs:
            (replacement_md, final) = data.get_data(field_name)
            if not duplicated and not final:
                # Duplicate this section if we need it for one of these
                # fields and we haven't already done it
                section.duplicate()
                duplicated = True
            if replacement_md is None:
                replacement_md = NONE_PARAGRAPH
            else:
                replaced_any = True
            if isinstance(replacement_md, str):
                replacement = markdown_to_plain_text(replacement_md)
            else:
                replacement = str(replacement_md)
            section.replace_field(field_name, replacement)
        if not replaced_any:
            section.remove_nonfirst_paragraphs()
            replacer = DocSectionParagraphReplacer(section)
            replacer.render_markdown(NONE_PARAGRAPH)

    def write(
        self,
        output_file: str,
        data: dict[str, list[str]],
        filter_referencers: MergeData.FilterReferencesCallable,
    ) -> None:
        """
        Write out a document based on the template.

        outputFile -- the filename to write to.
        data -- the data to place into the fields.
        filter_referencers -- see MergeData.__init__
        """
        self._interpolate_sections(
            self.top,
            MergeData(data, filter_referencers),
        )
        Path(output_file).parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self.docx.save(output_file)


def load_template(template_file: str) -> Document:
    """Load a template MS Word document."""
    return Document(template_file)
