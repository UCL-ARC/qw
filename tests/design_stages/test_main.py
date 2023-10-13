"""Testing main functionality of design stages."""
from qw.design_stages.main import Requirement, from_json


def test_build_from_json(
    json_minimal_requirement: str,
    minimal_requirement: Requirement,
):
    """Ensure that an instance can be serialised without any prior knowledge of the type."""
    built_from_json = from_json(json_minimal_requirement)
    assert isinstance(built_from_json, Requirement)
    assert minimal_requirement.diff(built_from_json) == {}
