"""Data types representing each design stage and funtions to interact with them."""
import json
from typing import Any, Self

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


def from_json(json_str: str) -> list[UserNeed | Requirement]:
    """
    Build design stages from json string.

    :param json_str: design stages serialised in a json array.
    :raises QwError: if a stage is unknown or has not been implemented
    :return: instances of classes, deserialised from json data
    """
    data_items = json.loads(json_str)
    output = []
    for data_item in data_items:
        output.append(_build_design_stage_or_throw(data_item))
    return output


def _build_design_stage_or_throw(data_item: dict[str, Any]):
    try:
        stage = DesignStage(data_item["stage"])
    except ValueError as exception:
        msg = (
            f"Design stage {data_item['stage']} not known, "
            f"should be one of {[stage.value for stage in DesignStage]}"
        )
        raise QwError(msg) from exception
    if stage == DesignStage.REQUIREMENT:
        return Requirement.from_dict(data_item)
    if stage == DesignStage.NEED:
        return UserNeed.from_dict(data_item)

    not_implemented = f"{stage} not implemented"
    raise QwError(not_implemented)
