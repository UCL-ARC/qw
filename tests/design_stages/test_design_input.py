"""Tests for design input functionality."""
import pytest

from qw.base import QwError
from qw.design_stages.input import DesignInput
from src.qw.design_stages.stages import DesignStage


def test_serialise() -> None:
    """
    Ensure serialisation.

    Given a design input instance with each required field being set to "qw_{field_name}"
    When this is serialised to json
    Then the output string should be a json representation of each required field with the value as "qw_{field_name}"
    """
    design_input = DesignInput()
    design_input.title = "qw_title"
    design_input.description = "qw_description"
    design_input._validate_required_fields()

    assert (
        design_input.to_json()
        == '{"title": "qw_title", "description": "qw_description", "user_need": null, "stage": "design-input"}'
    )


def test_deserialisation() -> None:
    """
    Ensure deserialisation.

    Given a design input instance with each required field being set to "qw_{field_name}"
    When this is serialised to json
    Then the output string should be a json representation of each required field with the value as "qw_{field_name}"
    """
    json_dump = '{"title": "qw_title", "description": "qw_description", "user_need": null , "stage": "design-input"}'

    design_input = DesignInput.from_json(json_dump)
    design_input._validate_required_fields()

    assert design_input.title == "qw_title"
    assert design_input.description == "qw_description"
    assert design_input.stage == DesignStage.INPUT


def test_required_fields() -> None:
    """Ensure exception is raised if a required field has not been set."""
    design_input = DesignInput()
    design_input.title = "qw_title"
    design_input.description = None
    with pytest.raises(QwError) as exception_info:
        design_input._validate_required_fields()
    assert "description" in str(exception_info.value)
