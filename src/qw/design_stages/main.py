"""Data types representing each design stage and functions to interact with them."""
from typing import Any, Self

from loguru import logger

from qw.base import QwError
from qw.design_stages._base import DesignBase
from qw.design_stages.categories import DesignStage, RemoteItemType
from qw.design_stages.checks import check
from qw.local_store.main import LocalStore
from qw.md import text_under_heading
from qw.remote_repo.service import Issue, PullRequest, Service


class UserNeed(DesignBase):
    """User need."""

    design_stage = DesignStage.NEED
    plural = "user_needs"

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
        instance.description = text_under_heading(issue.body, "Description", "no description")
        return instance

    @classmethod
    def is_dict_reference(cls, self_dict, from_stage_name):
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

    not_required_fields = frozenset(["user_need", "req_type", "component"])
    design_stage = DesignStage.REQUIREMENT
    plural = "requirements"

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
        instance.description = text_under_heading(issue.body, "Description", "no description")
        user_need = text_under_heading(issue.body, "Parent user need", "")
        if len(user_need) != 0:
            instance.user_need = user_need
        req_type = text_under_heading(issue.body, "Type of requirement", "")
        if len(req_type) != 0:
            instance.req_type = req_type
        component = text_under_heading(issue.body, "Component", "")
        if len(component) != 0:
            instance.component = component
        return instance

    @classmethod
    def is_dict_reference(cls, self_dict, from_stage_name):
        """
        Identify dicts that refer to self_dict.

        This could be a single Design Output or a single User Need.
        """
        if from_stage_name == DesignStage.NEED.value:
            internal_id = self_dict.get("user_need", None)
            if internal_id is None or internal_id[0] != "#":
                return None
            iid = internal_id[1:]
            if not iid.isnumeric():
                return None
            iid = int(iid)
            return lambda d: d.get("internal_id", None) == iid
        if from_stage_name == DesignStage.OUTPUT.value:
            internal_id = self_dict.get("internal_id", None)
            if internal_id is None:
                return None
            return lambda d: internal_id in d.get("closing_issues", [])
        return None

    @check(
        "User need links have qw-user-need label",
        "Requirement {0.internal_id} ({0.title}) has bad user need:",
        fail_item="{} is not labelled with qw-user-need",
    )
    def user_need_is_labelled_as_such(self, user_needs, **_kwargs) -> list[str]:
        """
        Test if the linked User Needs are actually labelled as qw-user-need.

        Design Outputs (PRs) have closing issues, and all these must refer
        to issues with the qw-requirement label (or qw-ignore).
        """
        if isinstance(self.user_need, str) and self.user_need.startswith("#"):
            un = self.user_need[1:]
            if un.isnumeric() and int(un) not in user_needs:
                return [self.user_need]
        return []

    @check(
        "User Need links must exist",
        "Requirement {0.internal_id} ({0.title}) has no user need:",
    )
    def user_need_must_exit(self, **_kwargs) -> bool:
        """Test if the User Needs are actually links to Github issues."""
        if (
            isinstance(self.user_need, str)
            and self.user_need.startswith("#")
            and self.user_need[1:].isnumeric()
        ):
            return False
        return True


class DesignOutput(DesignBase):
    """Output Design Stage."""

    design_stage = DesignStage.OUTPUT
    plural = "design_outputs"

    def __init__(self) -> None:
        """
        Initialize DesignOutput (internal only).

        Please use the from_markdown or from_dict methods instead of
        using this constructor.
        """
        super().__init__()
        self.requirement: str | None = None
        self.remote_item_type = RemoteItemType.REQUEST

    @classmethod
    def from_pr(cls, pr: PullRequest) -> Self:
        """
        Create design output from issue data.

        :param issue: pull request data from remote repository
        :return: DesignOutput instance
        """
        instance = cls()

        instance.title = pr.title
        instance.internal_id = pr.number
        instance.description = pr.body
        instance.closing_issues = pr.closing_issues
        return instance

    @classmethod
    def is_dict_reference(cls, self_dict, from_stage_name):
        """Identify Requirements dicts that self_dict referes to."""
        if from_stage_name != DesignStage.REQUIREMENT.value:
            return None
        requirements = self_dict.get("closing_issues", [])
        logger.debug("Requirements are: {}", requirements)
        return lambda d: d.get("internal_id", None) in requirements

    @check(
        "Closing Issues are Requirements",
        "Design Output {0.internal_id} ({0.title}) has bad closing issues:",
        fail_item="{} is not a requirement",
    )
    def closing_issues_are_requirements(
        self,
        requirements: dict[int, Requirement],
        **_kwargs,
    ) -> list[int]:
        """
        Test that closing issues are all Requirements.

        Design Outputs (PRs) have closing issues, and all these must refer
        to issues with the qw-requirement label (or qw-ignore).
        """
        failed: list[int] = []
        for req in self.closing_issues:
            if req not in requirements:
                failed.append(req)
        return failed


DESIGN_STAGE_CLASSES = DesignBase.__subclasses__()
_DESIGN_STAGE_CLASS_FROM_NAME = {
    ds_class.design_stage.value: ds_class for ds_class in DESIGN_STAGE_CLASSES
}


def get_design_stage_class_from_name(name: str) -> type[DesignBase] | None:
    """Get the subclass of DesignBase from a DesignStage enum value."""
    if name in _DESIGN_STAGE_CLASS_FROM_NAME:
        return _DESIGN_STAGE_CLASS_FROM_NAME[name]
    return None


DesignStages = list[UserNeed | Requirement | DesignOutput]


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
        # Could have multiple design stages from the same pull request
        # so allow multiple outputs from a single issue
        if "qw-user-need" in issue.labels:
            logger.debug("User Need #{}", issue.number)
            output_stages.append(UserNeed.from_issue(issue))
        elif "qw-requirement" in issue.labels:
            logger.debug("Requirement #{}", issue.number)
            output_stages.append(Requirement.from_issue(issue))
        else:
            logger.debug(
                "#{} is neither a User Need nor a Requirement",
                issue.number
            )
    for pr in service.pull_requests:
        if "qw-ignore" in issue.labels:
            logger.debug(
                "PR {number} tagged to be ignored, skipping",
                number=pr.number,
            )
            continue
        output_stages.append(DesignOutput.from_pr(pr))
        logger.debug("PR #{} added", pr.number)
    return output_stages
