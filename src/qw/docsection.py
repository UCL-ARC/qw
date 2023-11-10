"""
Layer over python-docx allowing looping through
outline sections, duplicating them as necessary
to put the required data in.
"""
import copy
import docx
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from loguru import logger
from lxml.etree import QName
import re
from typing import Self

from base import QwError
import md


def qname(ns : str, val : str) -> str:
    return QName(docx.oxml.ns.nsmap[ns], val)


def nsw(val : str) -> str:
    return qname("w", val)


MERGEFIELD_RE = re.compile(r"\s*MERGEFIELD\s+(.*?)\s*")
ATTRIB_ABSTRACTNUMID = nsw("abstractNumId")
ATTRIB_NUMID = nsw("numId")
ATTRIB_VAL = nsw("val")
ATTRIB_ASCII = nsw("ascii")
ATTRIB_HANSI = nsw("hAnsi")
ATTRIB_SPACE = qname("xml", "space")
TAG_R = nsw("r")
TAG_RPR = nsw("rPr")
TAG_B = nsw("b")
TAG_I = nsw("i")
TAG_RFONTS = nsw("rFonts")
TAG_T = nsw("t")
TAG_BR = nsw("br")
TAG_R_ID = qname("r", "id")
TAG_RSTYLE = nsw("rStyle")
TAG_P = nsw("p")
TAG_PPR = nsw("pPr")
TAG_PSTYLE = nsw("pStyle")
TAG_NUMPR = nsw("numPr")
TAG_ILVL = nsw("ilvl")
TAG_NUMID = nsw("numId")
TAG_BIDI = nsw("bidi")
TAG_JC = nsw("jc")


def is_fld_begin(run):
    return 0 < len(run.xpath('w:fldChar[@w:fldCharType="begin"]'))

def is_fld_separate(run):
    return 0 < len(run.xpath('w:fldChar[@w:fldCharType="separate"]'))

def is_fld_end(run):
    return 0 < len(run.xpath('w:fldChar[@w:fldCharType="end"]'))

HEADING_STYLE_ID = [
    "Heading1",
    "Heading2",
    "Heading3",
    "Heading4",
]

PREFORMATTED_FONT_NAME = "Courier"

class DocSection:
    """
    A section of an MS Word document; a list of contiguous
    paragraphs where the first paragraph has the lowest
    outline level.
    """
    def __init__(
        self,
        docx,
        from_index=None,
        outer_level=None,
        parent=None
    ):
        """
        Sets this DocSection as an empty object.
        `next` should be called to initialize.
        The section begins after the `after` element if set, or at
        the start of the document if not.
        The iteration ends at the end of the document or just before
        the first paragraph that has a level equal to or lower than
        outer_level (if not None)
        """
        self.docx = docx
        bodies = docx.element.xpath("w:body")
        if len(bodies) != 1:
            raise QwError("not a single body")
        self.element = bodies[0]
        self.start_index = from_index or 0
        self.end_index = self.start_index
        self.start_level = None
        self.outer_level = outer_level
        self.parent=parent

    def get_bullet_level(self, element):
        bullets = element.xpath('w:pPr/w:numPr/w:ilvl')
        if len(bullets) != 0:
            val = bullets[0].attrib[ATTRIB_VAL]
            if val.isnumeric():
                return int(val) + 50
            else:
                return 50
        return None

    def _get_paragraph_level(self, paragraph):
        # style outline level
        styles = paragraph.xpath('w:pPr/w:pStyle')
        if len(styles) != 0:
            style_id = styles[0].attrib[ATTRIB_VAL]
            style = self.docx.styles.get_by_id(style_id, docx.enum.style.WD_STYLE_TYPE.PARAGRAPH)
            outlines = style.element.xpath('w:pPr/w:outlineLvl')
            if len(outlines) != 0:
                val = outlines[0].attrib[ATTRIB_VAL]
                if val.isnumeric():
                    return int(val) - 50
            r = self.get_bullet_level(style.element)
            if r is not None:
                return r
        # bullet level
        r = self.get_bullet_level(paragraph)
        if r is not None:
            return r
        return 0

    def next(self):
        """
        Move to the next section in the document. Returns
        True if there is a next section at this level, False
        if not (and so we did not move on).
        """
        if self.at_document_end():
            return False
        self.start_index = self.end_index
        p = self.element[self.start_index]
        level = self._get_paragraph_level(p)
        if self.outer_level is not None and level <= self.outer_level:
            # We have finished this run of sections at this level
            return False
        if self.start_level is None or level < self.start_level:
            self.start_level = level
        p = p.getnext()
        self.last_head_paragraph_index = self.start_index
        self.end_index += 1
        while p is not None:
            level = self._get_paragraph_level(p)
            # Have we reached the end of the section?
            if level <= self.start_level:
                logger.debug("Section {0} - {1} (hit level {2} <= {3})", self.start_index, self.end_index, level, self.start_level)
                return True
            self.end_index += 1
            p = p.getnext()
        logger.debug("Section {0} - {1} (end of document)", self.start_index, self.end_index)
        return True

    def at_document_end(self):
        return len(self.element) <= self.end_index

    def deeper(self) -> Self | None:
        if self.end_index - self.start_index < 2:
            return None
        return DocSection(
            self.docx,
            from_index=self.start_index + 1,
            outer_level=self.start_level,
            parent=self
        )

    def duplicate(self):
        """
        Adds a copy of this section after it.
        """
        length = self.end_index - self.start_index
        for i in range(length):
            p = copy.deepcopy(self.element[self.start_index + i])
            self.element.insert(self.end_index + i, p)
        if self.parent is not None:
            self.parent._paragraph_count_changed(length)

    def _paragraph_count_changed(self, length):
        self.end_index += length
        if self.parent is not None:
            self.parent._paragraph_count_changed(length)

    def fields(self) -> set[str]:
        """
        Returns a set of all the fields present in the first
        paragraph of this section.
        """
        r = set()
        if self.end_index == self.start_index:
            return r
        for instr in self.element[self.start_index].xpath('*/w:instrText'):
            merge = MERGEFIELD_RE.fullmatch(instr.text)
            if merge is not None:
                r.add(merge.group(1))
        return r

    def paragraph_is_only_field(self) -> bool:
        """
        Returns True if there is exactly one field in the first
        paragraph of this section (with no other text) and it is
        normal body text
        """
        if self.end_index == self.start_index:
            return False
        paragraph = self.element[self.start_index]
        if self._get_paragraph_level(paragraph) != 0:
            return False
        is_in_field = False
        for run in paragraph.xpath('w:r'):
            if is_fld_begin(run):
                is_in_field = True
            else:
                if not is_in_field:
                    return False
                if is_fld_end(run):
                    is_in_field = False
        return True

    def remove_nonhead_paragraphs(
        self
    ):
        """
        Remove all but the head paragraph of this section
        """
        start = self.start_index + 1
        length = self.end_index - start
        if length < 0:
            return
        for i in range(length):
            self.element.remove(self.element[start])
        if self.parent:
            self.parent._paragraph_count_changed(-length)

    def replace_head_paragraph(
        self,
        typ : md.DocumentBuilder.ParagraphType,
        level : int=0
    ):
        """
        Replace the first paragraph in the section with an empty
        paragraph of the required type.

        `level` is the level of the heading (0 = Heading 1)
        or bullet/numbered list element (0 = top)
        """
        p = self.element[self.start_index]
        p.clear()
        self._add_paragraph_style(typ, level, p)

    def _get_num_id(self, fmt):
        """
        Get the numId required for the bullet style
        we want. We are assuming that we only need any
        arbitrary one.
        """
        numbering = self.docx.part.numbering_part.element
        numFmts = numbering.xpath(
            'w:abstractNum/w:lvl/w:numFmt[@w:val="{0}"]'.format(fmt)
        )
        if len(numFmts) == 0:
            return None
        abstractNumId = numFmts[0].getparent().getparent().attrib[ATTRIB_ABSTRACTNUMID]
        nums = numbering.xpath(
            'w:num/w:abstractNumId[@w:val="{0}"]'.format(abstractNumId)
        )
        if len(nums) == 0:
            return None
        numId = nums[0].getparent().attrib[ATTRIB_NUMID]
        return numId

    def _add_paragraph_style(self, typ, level, paragraph):
        pPr = paragraph.makeelement(TAG_PPR)
        paragraph.append(pPr)
        numId = None
        styleName = None
        if typ is None:
            styleName = "Normal"
        elif typ == md.DocumentBuilder.ParagraphType.HEADING:
            if 0 <= level and level < len(HEADING_STYLE_ID):
                styleName = HEADING_STYLE_ID[level]
        elif typ == md.DocumentBuilder.ParagraphType.LIST_ORDERED:
            styleName = "Normal"
            numId = self._get_num_id("decimal")
        elif typ == md.DocumentBuilder.ParagraphType.LIST_UNORDERED:
            styleName = "Normal"
            numId = self._get_num_id("bullet")
        if styleName is not None:
            pPr.append(
                paragraph.makeelement(TAG_PSTYLE, { ATTRIB_VAL: styleName }),
            )
        if numId is not None:
            numPr = paragraph.makeelement(TAG_NUMPR)
            numPr.extend([
                paragraph.makeelement(TAG_ILVL, { ATTRIB_VAL: str(level) }),
                paragraph.makeelement(TAG_NUMID, { ATTRIB_VAL: numId })
            ])
            pPr.append(numPr)
        pPr.extend([
            paragraph.makeelement(TAG_BIDI, { ATTRIB_VAL: "0" }),
            paragraph.makeelement(TAG_JC, { ATTRIB_VAL: "left" }),
            paragraph.makeelement(TAG_RPR),
        ])

    def add_run(
        self,
        text : str,
        bold : bool=None,
        italic : bool=None,
        pre : bool=None
    ):
        """
        Add a run to the last added paragraph
        """
        if not text:
            return
        p = self.element[self.last_head_paragraph_index]
        r = p.makeelement(TAG_R)
        p.append(r)
        rPr = p.makeelement(TAG_RPR)
        if bold:
            rPr.extend(rPr.makeelement(TAG_B))
        if italic:
            rPr.append(rPr.makeelement(TAG_I))
        if pre:
            rPr.append(rPr.makeelement(TAG_RFONTS, {
                ATTRIB_ASCII: PREFORMATTED_FONT_NAME,
                ATTRIB_HANSI: PREFORMATTED_FONT_NAME
            }))
        r.append(rPr)
        self._add_plain_text(r, text)

    def _add_plain_text(self, r, text):
        br = False
        for text_line in text.splitlines():
            if br:
                r.append(r.makeelement(TAG_BR))
            else:
                br = True
            t = r.makeelement(TAG_T, { ATTRIB_SPACE: "preserve" })
            t.text = text_line
            r.append(t)

    def _get_link_id(self, link : str):
        # find an existing link
        max_id_so_far = 0
        for rid, rel in self.docx.part.rels.items:
            if rel.target_ref == link:
                return rid
            # Looking for IDs of the form rId<n> so that we can
            # avoid clashing our own id with any existing ids
            parts = rid.split("rId")
            if len(parts) == 2 and parts[1].isnumeric():
                max_id_so_far = max(max_id_so_far, int(parts[1]))
        # add a new link
        rid = "rId" + (max_id_so_far + 1)
        self.docx.part.rels.add_relationship(RT.HYPERLINK, link, rid)
        return rid

    def add_hyperlink(
        self,
        text : str,
        link : str
    ):
        p = self.element[self.last_head_paragraph_index]
        rid = self._get_link_id(link)
        hyperlink = p.makeelement(TAG_R, { TAG_R_ID: rid })
        r = p.append(hyperlink)
        rPr = p.makeelement(TAG_RPR)
        rStyle = p.makeelement(TAG_RSTYLE, {
            ATTRIB_VAL: "InternetLink"
        })
        rPr.append(rStyle)
        t = p.makeelement(TAG_T)
        t.text = text
        r.extend([rPr, t])

    def add_paragraph(
        self,
        typ : md.DocumentBuilder.ParagraphType,
        level : int=0
    ):
        p = self.element.makeelement(TAG_P)
        self._add_paragraph_style(typ, level, p)
        self.last_head_paragraph_index += 1
        self.element.insert(
            self.last_head_paragraph_index,
            p
        )

    def _delete_backwards_until(self, node, predicate):
        go_next = lambda n: n.getprevious()
        return self._delete_direction_until(node, predicate, go_next)

    def _delete_forwards_until(self, node, predicate):
        go_next = lambda n: n.getnext()
        return self._delete_direction_until(node, predicate, go_next)

    def _delete_direction_until(self, node, predicate, go_next):
        while node is not None:
            next = go_next(node)
            at_end = predicate(node)
            node.getparent().remove(node)
            if at_end:
                return next
            node = next

    def replace_field(self, name : str, plain_text : str):
        for instr in self.element[self.start_index].xpath('*/w:instrText'):
            merge = MERGEFIELD_RE.fullmatch(instr.text)
            if merge is not None:
                if merge.group(1) == name:
                    # find the start of the field
                    r = instr.getparent()
                    self._delete_backwards_until(r.getprevious(), is_fld_begin)
                    r = self._delete_forwards_until(r, is_fld_separate)
                    if r is not None:
                        for t in r.xpath("w:t"):
                            r.remove(t)
                        self._add_plain_text(r, plain_text)
                        self._delete_forwards_until(r.getnext(), is_fld_end)


class DocSectionParagraphReplacer(md.DocumentBuilder):

    def __init__(self, section : DocSection):
        self.section = section
        self.first = True

    def new_paragraph(
        self,
        paragraph_type : md.DocumentBuilder.ParagraphType=None,
        paragraph_level : int=0
    ):
        if self.first:
            self.section.replace_head_paragraph(paragraph_type, paragraph_level)
            self.first = False
        else:
            self.section.add_paragraph(paragraph_type, paragraph_level)

    def add_run(self, text : str, bold : bool=None, italic : bool=None, pre : bool=None):
        self.section.add_run(text, bold, italic, pre)

    def add_hyperlink(self, text : str, link : str, bold : bool=None, italic : bool=None, pre : bool=None):
        self.section.add_hyperlink(text, link)
