"""Tests for requirement functionality."""
import copy

import pytest

from qw.base import QwError
from qw.design_stages.main import Requirement


def test_serialise(
    dict_minimal_requirement: dict,
    minimal_requirement: Requirement,
) -> None:
    """
    Ensure serialisation.

    Given a requirement instance with each required field being set to "qw_{field_name}"
    When this is serialised to json
    Then the output string should be a json representation of each required field with the value as "qw_{field_name}"
    """
    assert minimal_requirement.to_dict() == dict_minimal_requirement


def test_required_fields() -> None:
    """Ensure exception is raised if a required field has not been set."""
    requirement = Requirement()
    requirement.title = "qw_title"
    requirement.description = None
    with pytest.raises(QwError) as exception_info:
        requirement._validate_required_fields()
    assert "description" in str(exception_info.value)


def test_differences(minimal_requirement) -> None:
    """Test that a difference can be rendered detected."""
    original = copy.copy(minimal_requirement)
    changed = copy.copy(minimal_requirement)
    original.description = "qw_description\n\nover\nlines"
    changed.description = "q_description\n\nmany lines"
    diff = changed.diff(original)

    assert diff == {
        "description": {"self": changed.description, "other": original.description},
    }
