"""Data types representing each design stage and functions to interact with them."""
import json
from typing import Any, Self

from loguru import logger

from qw.base import QwError
from qw.design_stages._base import DesignBase
from qw.design_stages.categories import DesignStage, RemoteItemType
from qw.md import text_under_heading
from qw.remote_repo.service import Issue, Service


class UserNeed(DesignBase):
    """User need."""

    not_required_fields = frozenset(["requirement"])

    def __init__(self) -> None:
        """Please use the from_markdown or from_dict methods instead of using this constructor."""
        super().__init__()
        self.requirement: str | None = None
        self.remote_item_type = RemoteItemType.ISSUE
        self.stage = DesignStage.NEED

    @classmethod
    def from_issue(cls, issue: Issue) -> Self:
        """
        Create requirement from issue data.

        :param issue: issue data from remote repository
        :return: Requirement instance
        """
        instance = cls()

        instance.title = issue.title
        instance.internal_id = issue.number
        instance.description = text_under_heading(issue.body, "Description")
        instance.requirement = text_under_heading(issue.body, "Requirements")
        return instance


class Requirement(DesignBase):
    """Requirement Design stage."""

    not_required_fields = frozenset(["user_need"])

    def __init__(self) -> None:
        """Please use the from_markdown or from_dict methods instead of using this constructor."""
        super().__init__()
        self.user_need: str | None = None
        self.remote_item_type = RemoteItemType.ISSUE
        self.stage = DesignStage.REQUIREMENT

    @classmethod
    def from_issue(cls, issue: Issue) -> Self:
        """
        Create requirement from issue data.

        :param issue: issue data from remote repository
        :return: Requirement instance
        """
        instance = cls()

        instance.title = issue.title
        instance.internal_id = issue.number
        instance.description = text_under_heading(issue.body, "Description")
        instance.user_need = text_under_heading(issue.body, "Parent user need")
        return instance


DesignStages = list[UserNeed | Requirement]


def from_json(json_str: str) -> DesignStages:
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


def from_service(service: Service) -> DesignStages:
    """
    Build design stages from a given service.

    :param service: instance of a service for a remote repo.
    :return: all designs stages
    """
    output_stages = []
    for issue in service.issues:
        if "qw-ignore" in issue.labels:
            logger.debug(
                "Issue {number} tagged to be ignored, skipping",
                number=issue.number,
            )
            continue
        # Could have multiple design stages from the same pull request so allow multiple outputs from a single issue
        if "qw-user-need" in issue.labels:
            output_stages.append(UserNeed.from_issue(issue))
        if "qw-requirement" in issue.labels:
            output_stages.append(Requirement.from_issue(issue))
    return output_stages
