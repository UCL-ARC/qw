"""Testing main functionality of design stages."""
import json

import pytest

from qw.base import QwError
from qw.design_stages.main import Requirement, from_json


def test_build_from_json(
    json_minimal_requirement: str,
    minimal_requirement: Requirement,
):
    """Ensure that an instance can be serialised without any prior knowledge of the type."""
    built_from_json = from_json(json_minimal_requirement)
    assert isinstance(built_from_json, Requirement)
    assert minimal_requirement.diff(built_from_json) == {}


def test_unknown_type_from_json(json_minimal_requirement: str):
    """An unknown design stage in the json should raise a QwException."""
    json_dict = json.loads(json_minimal_requirement)
    json_dict["stage"] = "unknown"
    unknown_json_dump = json.dumps(json_dict)
    with pytest.raises(QwError):
        from_json(unknown_json_dump)
