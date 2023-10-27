"""Testing main functionality of design stages."""
import json

import pytest

from qw.base import QwError
from qw.design_stages.main import Requirement, from_json, get_remote_stages
from tests.helpers.mock_service import FileSystemService


def test_build_from_dict(
    dict_minimal_requirement: dict,
    minimal_requirement: Requirement,
):
    """Ensure that an instance can be serialised without any prior knowledge of the type."""
    json_data = json.dumps([dict_minimal_requirement])
    built_from_json = from_json(json_data)
    assert len(built_from_json) == 1
    assert isinstance(built_from_json[0], Requirement)
    assert minimal_requirement.diff(built_from_json[0]) == {}


def test_unknown_type_from_json(dict_minimal_requirement: dict):
    """An unknown design stage in the dictionary should raise a QwException."""
    dict_minimal_requirement["stage"] = "unknown"
    unknown_json_dump = json.dumps([dict_minimal_requirement])
    with pytest.raises(QwError):
        from_json(unknown_json_dump)


def test_filesystem_service_builds_requirement():
    """
    Given a single requirement is serialised to file and a filesystem service is built for the resource directory.

    When the requirement is parsed from the service
    Then there should be one Requirement from the service
    """
    service = FileSystemService("single_requirement")
    stages = get_remote_stages(service)
    assert len(stages) == 1
