"""Shared fixtures for design stage testing."""

import pytest

from qw.design_stages.main import Requirement


@pytest.fixture()
def dict_minimal_requirement() -> dict:
    """Build dict of minimal requirement."""
    return {
        "title": "Calculate warfarin",
        "description": "Warfarin dosage should be calculated using based on patient age, gender and weight",
        "internal_id": 6,
        "remote_item_type": "issue",
        "stage": "requirement",
        "user_need": "#5",
        "version": 1,
    }


@pytest.fixture()
def minimal_requirement() -> Requirement:
    """Python object for minimal requirement."""
    requirement = Requirement()
    requirement.title = "Calculate warfarin"
    requirement.description = "Warfarin dosage should be calculated using based on patient age, gender and weight"
    requirement.internal_id = 6
    requirement.user_need = "#5"
    requirement.version = 1
    requirement._validate_required_fields()
    return requirement
