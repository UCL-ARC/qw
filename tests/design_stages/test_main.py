"""Testing main functionality of design stages."""
from pathlib import Path

import pytest

from qw.base import QwError
from qw.design_stages.main import Requirement, get_local_stages, get_remote_stages
from qw.remote_repo.test_service import FileSystemService


def test_build_from_dict(
    dict_minimal_requirement: dict,
    minimal_requirement: Requirement,
    qw_store_builder,
):
    """Ensure that an instance can be deserialised without any prior knowledge of the type."""
    store = qw_store_builder([dict_minimal_requirement])
    stages = get_local_stages(store)
    assert len(stages) == 1
    assert isinstance(stages[0], Requirement)
    assert minimal_requirement.diff(stages[0]) == {}


def test_unknown_type_from_json(dict_minimal_requirement: dict, qw_store_builder):
    """An unknown design stage in the input data should raise a QwException."""
    dict_minimal_requirement["stage"] = "unknown"
    store = qw_store_builder([dict_minimal_requirement])
    with pytest.raises(QwError):
        get_local_stages(store)


def test_filesystem_service_builds_requirement():
    """
    Given a single requirement is serialised to file and a filesystem service is built for the resource directory.

    When the requirement is parsed from the service
    Then there should be one Requirement from the service
    """
    service = FileSystemService(
        Path(__file__).parents[1] / "resources" / "design_stages",
        "single_requirement",
    )
    stages = get_remote_stages(service)
    assert len(stages) == 1
