"""Base class for design stages."""
import re
from abc import ABC
from collections.abc import Callable
from copy import copy
from typing import Any, Self

from qw.base import QwError
from qw.design_stages.categories import DesignStage, RemoteItemType


class DesignBase(ABC):
    """Design stage base class."""

    # to be overriden by child classes for specific fields that are allowed to be empty.
    not_required_fields: frozenset[str] = frozenset()
    base_fields: frozenset[str] = frozenset(
        ["title", "description", "internal_id", "version"],
    )
    design_stage: DesignStage | None = None

    LINK_RE = re.compile(r"#(\d+)")

    def __init__(self) -> None:
        """Shared fields for all design stage classes."""
        self.title: str | None = None
        self.description: str | None = None
        self.internal_id: int | None = None
        self.remote_item_type: RemoteItemType | None = None
        self.stage: DesignStage | None = self.design_stage
        self.version = 1

    def __repr__(self):
        """User-friendly representation of Design stage class."""
        return f"<{self.__class__.__name__} #{self.internal_id}: {self.title}>"

    def _validate_required_fields(self):
        not_required = ["not_required_fields", *self.not_required_fields]
        for field, value in self.__dict__.items():
            if field in not_required:
                continue
            if not value:
                msg = f"No {field} in {self.__class__.__name__}"
                raise QwError(msg)

    def get_links_from_text(self, text) -> list[int]:
        """Get #IDs contained in text."""
        if text is None:
            return []
        return [int(match) for match in self.LINK_RE.findall(text)]

    def to_dict(self) -> dict[str, Any]:
        """
        Serialise data to dictionary.

        Does not serialise class fields as these may be changed in later versions

        :return: JSON representation of class
        """
        return copy(self.__dict__)

    @classmethod
    def from_dict(cls, input_dict: dict[str, Any]) -> Self:
        """
        Build class instance from dictionary.

        :param input_dict: instance persisted to dictionary.
        :return: Design stage instance.
        """
        instance = cls()
        for key, value in input_dict.items():
            if key == "stage":
                continue
            if key == "remote_item_type":
                instance.remote_item_type = RemoteItemType(value)
                continue
            instance.__dict__[key] = value

        return instance

    @classmethod
    def is_dict_reference(
        cls,
        _self_dict: dict[str, Any],
        _from_stage_name: str,
    ) -> Callable[[dict[str, Any]], bool] | None:
        """
        Identify dicts from objects that reference this one.

        Let s be an object of this Self type, and fset be a set of
        objects of class F, a different subclass of DesignBase.
        Then self_dict = s.to_dict(),
        from_stage_name = F.design_stage.value.

        This function returns a predicate p. For each element f of
        fset, p(f.to_dict()) returns True if (and only if) f refers
        to s.

        Returns None instead of a function that always returns False.
        """
        return None

    def diff(self, other: Self) -> dict[str, dict[str, str]]:
        """
        Compare the data of each field with another instance,  returning the fields with differences only.

        Ignores the version number and deleted flag as these are only stored locally.

        :param other: Another instance of the same class
        :raises ValueError: if other is not the same class as self.
        :return: A dictionary with each field that was different, with the `self` and `other` string values.
        """
        if not isinstance(other, type(self)):
            msg = "Instances must be of the same class type."
            raise ValueError(msg)

        output_fields = {}
        for field_name in self.__dict__:
            if field_name in ["version", "deleted"]:
                continue
            self_data = getattr(self, field_name)
            other_data = getattr(other, field_name)

            if self_data != other_data:
                output_fields[field_name] = {"self": str(self_data)}
                output_fields[field_name]["other"] = str(other_data)

        return output_fields

    def mark_as_deleted(self):
        self.deleted = True

    def is_marked_deleted(self):
        return hasattr(self, "deleted") and self.deleted
