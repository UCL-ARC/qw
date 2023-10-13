"""Data types representing each design stage."""
from typing import Self

from qw.design_stages._base import DesignBase
from qw.md import text_under_heading
from src.qw.design_stages.categories import DesignStage, RemoteItemType


class Requirement(DesignBase):
    """Requirement Design stage."""

    not_required_fields = frozenset(["user_need"])

    def __init__(self) -> None:
        """Please use the from_markdown or from_json methods instead of using this constructor."""
        super().__init__()
        self.user_need: str | None = None
        self.remote_item_type = RemoteItemType.ISSUE
        self.stage = DesignStage.REQUIREMENT

    @classmethod
    def from_markdown(cls, title: str, internal_id: int, markdown: str) -> Self:
        """
        Create requirement from Markdown data.

        :param title: title of the requirement
        :param internal_id: Internal ID of the requirement, e.g. GitHub id
        :param markdown: Markdown text within the issue
        :return: Requirement instance
        """
        instance = cls()

        instance.title = title
        instance.internal_id = internal_id
        instance.description = text_under_heading(markdown, "Description")
        instance.user_need = text_under_heading(markdown, "Parent user need")
        return instance
