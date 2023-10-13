"""Base class for design stages."""
import json
from abc import abstractmethod
from copy import copy
from typing import Self

from qw.base import QwError
from qw.design_stages.categories import RemoteItemType


class DesignBase:
    """Design stage base class."""

    # to be overriden by child classes for specific fields that are allowed to be empty.
    not_required_fields: frozenset[str] = frozenset()

    def __init__(self) -> None:
        """Shared fields for all design stage classes."""
        self.title: str | None = None
        self.description: str | None = None
        self.internal_id: int | None = None
        self.remote_item_type: RemoteItemType | None = None
        self.stage: DesignBase | None = None

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

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """
        Build json from json string.

        :param json_str: json string representation
        :return: Design stage instance.
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

    @classmethod
    @abstractmethod
    def from_markdown(cls, title: str, internal_id: int, markdown: str) -> Self:
        """
        Create design stage from Markdown data.

        :param title: title of the requirement
        :param internal_id: Internal ID of the requirement, e.g. GitHub id
        :param markdown: Markdown text within the issue
        :return: Requirement instance
        """
