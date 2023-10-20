"""Base class for design stages."""
import json
from abc import ABC, abstractmethod
from copy import copy
from typing import Self

from qw.base import QwError
from qw.design_stages.categories import RemoteItemType


class DesignBase(ABC):
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

    def diff(self, other: Self) -> dict[str, dict[str, str]]:
        """
        Compare the data of each field with another instance,  returning the fields with differences only.

        :param other: Another instance of the same class
        :raises ValueError: if other is not the same class as self.
        :return: A dictionary with each field that was different, with the `self` and `other` string values.
        """
        if not isinstance(other, type(self)):
            msg = "Instances must be of the same class type."
            raise ValueError(msg)

        output_fields = {}
        for field_name in self.__dict__:
            self_data = getattr(self, field_name)
            other_data = getattr(other, field_name)

            if self_data != other_data:
                output_fields[field_name] = {"self": str(self_data)}
                output_fields[field_name]["other"] = str(other_data)

        return output_fields

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
