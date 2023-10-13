"""Design requirement and any specific functionality."""
import json
from copy import copy
from typing import Self

from qw.base import QwError
from qw.md import text_under_heading
from src.qw.design_stages.categories import DesignStage, RemoteItemType


class Requirement:
    """Requirement."""

    not_required_fields = frozenset(["user_need"])

    def __init__(self) -> None:
        """Please use the from_markdown or from_json methods instead of using this constructor."""
        self.title: str | None = None
        self.description: str | None = None
        self.user_need: str | None = None
        self.internal_id: int | None = None
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

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """
        Build json from json string.

        :param json_str: json string representation
        :return: Requirement instance.
        """
        instance = cls()
        json_data = json.loads(json_str)
        for key, value in json_data.items():
            if key == "stage":
                continue
            if key == "remote_item_type":
                instance.remote_item_type = RemoteItemType(value)
                continue
            instance.__dict__[key] = value

        return instance

    def _validate_required_fields(self):
        not_required = ["not_required_fields", *self.not_required_fields]
        for field, value in self.__dict__.items():
            if field in not_required:
                continue
            if not value:
                msg = f"No {field} in {self.__class__.__name__}"
                raise QwError(msg)

    def to_json(self) -> str:
        """
        Serialise data to JSON.

        Does not serialise class fields as these may be changed in later versions

        :return: JSON representation of class
        """
        serialise_dict = copy(self.__dict__)
        return json.dumps(serialise_dict)
