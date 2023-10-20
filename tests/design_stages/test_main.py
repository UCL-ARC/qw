"""Testing main functionality of design stages."""
import json

import pytest

from qw.base import QwError
from qw.design_stages.main import Requirement, from_json


def test_build_from_dict(
    dict_minimal_requirement: dict,
    minimal_requirement: Requirement,
):
    """Ensure that an instance can be serialised without any prior knowledge of the type."""
    json_data = json.dumps(dict_minimal_requirement)
    built_from_json = from_json(json_data)
    assert isinstance(built_from_json, Requirement)
    assert minimal_requirement.diff(built_from_json) == {}


def test_unknown_type_from_json(dict_minimal_requirement: dict):
    """An unknown design stage in the dictionary should raise a QwException."""
    dict_minimal_requirement["stage"] = "unknown"
    unknown_json_dump = json.dumps(dict_minimal_requirement)
    with pytest.raises(QwError):
        from_json(unknown_json_dump)
