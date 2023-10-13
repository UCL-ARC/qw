"""Tests for requirement functionality."""
import json

import pytest

from qw.base import QwError
from qw.design_stages.requirement import Requirement
from src.qw.design_stages.categories import DesignStage


@pytest.fixture()
def json_dump():
    """JSON dump of requirement."""
    json_data = {
        "title": "qw_title",
        "description": "qw_description",
        "user_need": None,
        "internal_id": 1,
        "remote_item_type": "issue",
        "stage": "requirement",
    }
    return json.dumps(json_data)


def test_serialise(json_dump) -> None:
    """
    Ensure serialisation.

    Given a requirement instance with each required field being set to "qw_{field_name}"
    When this is serialised to json
    Then the output string should be a json representation of each required field with the value as "qw_{field_name}"
    """
    requirement = Requirement()
    requirement.title = "qw_title"
    requirement.description = "qw_description"
    requirement.internal_id = 1
    requirement._validate_required_fields()

    assert requirement.to_json() == json_dump


def test_deserialisation(json_dump) -> None:
    """
    Ensure deserialisation.

    Given a requirement instance with each required field being set to "qw_{field_name}"
    When this is serialised to json
    Then the output string should be a json representation of each required field with the value as "qw_{field_name}"
    """
    requirement = Requirement.from_json(json_dump)
    requirement._validate_required_fields()

    assert requirement.title == "qw_title"
    assert requirement.description == "qw_description"
    assert requirement.internal_id == 1
    assert requirement.stage == DesignStage.REQUIREMENT


def test_required_fields() -> None:
    """Ensure exception is raised if a required field has not been set."""
    requirement = Requirement()
    requirement.title = "qw_title"
    requirement.description = None
    with pytest.raises(QwError) as exception_info:
        requirement._validate_required_fields()
    assert "description" in str(exception_info.value)
