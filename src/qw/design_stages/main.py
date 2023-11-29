"""Data types representing each design stage and functions to interact with them."""
from typing import Any, Self

from loguru import logger

from qw.base import QwError
from qw.design_stages._base import DesignBase
from qw.design_stages.categories import DesignStage, RemoteItemType
from qw.local_store.main import LocalStore
from qw.md import text_under_heading
from qw.remote_repo.service import Issue, Service


class UserNeed(DesignBase):
    """User need."""

    not_required_fields = frozenset(["requirement"])
    design_stage = DesignStage.NEED

    def __init__(self) -> None:
        """Please use the from_markdown or from_dict methods instead of using this constructor."""
        super().__init__()
        self.requirement: str | None = None
        self.remote_item_type = RemoteItemType.ISSUE

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

    @classmethod
    def is_dict_backreference(cls, self_dict, from_stage_name):
        """Identify Requirements dicts that refer to self_dict."""
        logger.debug("User Need backreferences from {}?", from_stage_name)
        if from_stage_name != DesignStage.REQUIREMENT.value:
            logger.debug("No")
            return None
        internal_id = self_dict.get("internal_id", None)
        if internal_id is None:
            logger.debug("No internal_id!")
            return None
        iid = f"#{internal_id}"
        logger.debug("Looking for .user_need == {}", iid)
        return lambda d: d.get("user_need", None) == iid


class Requirement(DesignBase):
    """Requirement Design stage."""

    not_required_fields = frozenset(["user_need"])
    design_stage = DesignStage.REQUIREMENT

    def __init__(self) -> None:
        """Please use the from_markdown or from_dict methods instead of using this constructor."""
        super().__init__()
        self.user_need: str | None = None
        self.remote_item_type = RemoteItemType.ISSUE

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


_DESIGN_STAGE_CLASS = {
    ds_class.design_stage.value: ds_class for ds_class in DesignBase.__subclasses__()
}


def get_design_stage_class_from_name(name: str) -> type[DesignBase] | None:
    """Get the subclass of DesignBase from a DesignStage enum value."""
    if name in _DESIGN_STAGE_CLASS:
        return _DESIGN_STAGE_CLASS[name]
    return None


DesignStages = list[UserNeed | Requirement]


def get_local_stages(local_store: LocalStore) -> DesignStages:
    """
    Build design stages from local store.

    :param local_store: local storage
    :raises QwError: if a stage is unknown or has not been implemented
    :return: instances of classes, deserialised from local store
    """
    data_items = local_store.read_local_data()
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
    design_stage_class = get_design_stage_class_from_name(stage)
    if design_stage_class is not None:
        return design_stage_class.from_dict(data_item)

    not_implemented = f"{stage} not implemented"
    raise QwError(not_implemented)


def get_remote_stages(service: Service) -> DesignStages:
    """
    Build design stages from a given remote service.

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
