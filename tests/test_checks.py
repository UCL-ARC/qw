"""Test check behaviour"""
import pytest

from qw.cli import run_checks_with_impacts
from qw.design_stages.main import get_local_stages

@pytest.mark.parametrize(
    ("empty_local_store", "test_design_stages", "expected_error_count", "expected_warning_count"), [
        ({ "checks": {
            "User need links have qw-user-need label": "warning",
            "User Need links must exist": "error",
            "Closing Issues are Requirements": "off",
        }}, "incorrect_links", 1, 2),
        ({ "checks": {
            "User need links have qw-user-need label": "off",
            "User Need links must exist": "off",
            "Closing Issues are Requirements": "warning",
        }}, "incorrect_links", 0, 2),
    ],
    indirect=["empty_local_store", "test_design_stages"],
)
def test_check_severity(
    qw_store_builder,
    test_design_stages,
    expected_error_count,
    expected_warning_count,
):
    store = qw_store_builder(test_design_stages)
    stages = get_local_stages(store)
    results = run_checks_with_impacts(store, stages)
    assert results.object_count == 6
    assert len(results.errors) == expected_error_count
    assert len(results.warnings) == expected_warning_count
