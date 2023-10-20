"""Data types representing each design stage and funtions to interact with them."""
import json
from typing import Self

from qw.base import QwError
from qw.design_stages._base import DesignBase
from qw.design_stages.categories import DesignStage, RemoteItemType
from qw.md import text_under_heading


class UserNeed(DesignBase):
    """User need."""

    not_required_fields = frozenset(["requirement"])

    def __init__(self) -> None:
        """Please use the from_markdown or from_json methods instead of using this constructor."""
        super().__init__()
        self.requirement: str | None = None
        self.remote_item_type = RemoteItemType.ISSUE
        self.stage = DesignStage.NEED

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
        instance.requirement = text_under_heading(markdown, "Requirements")
        return instance


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


def from_json(json_str: str) -> UserNeed | Requirement:
    """
    Build any design stage from json.

    :param json_str: design stage serialised in json.
    :raises QwError: if the stage is unknown or has not been implemented
    :return: instance of class with the json data
    """
    json_data = json.loads(json_str)
    msg = f"Design stage {json_data['stage']} not known, should be one of {[stage.value for stage in DesignStage]}"
    try:
        stage = DesignStage(json_data["stage"])
    except ValueError as exception:
        raise QwError(msg) from exception

    if stage == DesignStage.REQUIREMENT:
        return Requirement.from_dict(json_data)
    if stage == DesignStage.NEED:
        return UserNeed.from_dict(json_data)
    not_implemented = f"{stage} not implemented"
    raise QwError(not_implemented)
