"""Testing of common service functions."""
import pytest

from qw.design_stages.main import Requirement


@pytest.mark.parametrize(
    ("store", "results"),
    [
        (
            {
                "component": "System",
                "description": "Desc",
                "internal_id": 4,
                "remote_item_type": "issue",
                "req_type": "Functional",
                "stage": "requirement",
                "title": "Control",
                "user_need": "#45",
                "version": 1,
            },
            [45],
        ),
        (
            {
                "component": "System",
                "description": "Desc",
                "internal_id": 5,
                "remote_item_type": "issue",
                "req_type": "Functional",
                "stage": "requirement",
                "title": "Control",
                "user_need": "Mostly #34 but also #322. #76 and #119",
                "version": 1,
            },
            [34, 322, 76, 119],
        ),
        (
            {
                "component": "System",
                "description": "Desc",
                "internal_id": 6,
                "remote_item_type": "issue",
                "req_type": "Functional",
                "stage": "requirement",
                "title": "Control",
                "user_need": "#1\n#2",
                "version": 2,
            },
            [1, 2],
        ),
    ],
)
def test_requirement_user_need_links(store, results):
    """Test requirement's user need links are extracted."""
    req = Requirement.from_dict(store)
    assert results == req.user_need_links()
