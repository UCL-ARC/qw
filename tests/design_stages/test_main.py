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


def test_filesystem_service_builds_issues():
    """
    File system service should load issues from test resources directory.

    Given no parent directory has been defined and a filesystem service has been created
    When the issues are parsed from the service
    Then there should be at least one DesignStage from the service
    """
    service = FileSystemService()
    stages = get_remote_stages(service)
    assert stages
