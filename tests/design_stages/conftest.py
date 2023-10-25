"""Shared fixtures for design stage testing."""

import pytest

from qw.design_stages.main import Requirement


@pytest.fixture()
def dict_minimal_requirement() -> dict:
    """JSON dump of minimal requirement."""
    return {
        "title": "qw_title",
        "description": "qw_description\n\nover\nlines",
        "internal_id": 1,
        "remote_item_type": "issue",
        "stage": "requirement",
        "user_need": None,
    }


@pytest.fixture()
def minimal_requirement() -> Requirement:
    """Python object for minimal requirement."""
    requirement = Requirement()
    requirement.title = "qw_title"
    requirement.description = "qw_description\n\nover\nlines"
    requirement.internal_id = 1
    requirement._validate_required_fields()
    return requirement
