"""Test for changes."""
from pathlib import Path

import pytest

from qw.changes import ChangeHandler
from qw.remote_repo.test_service import FileSystemService


def handler_with_single_requirement(store, base_dir=None) -> ChangeHandler:
    """Build ChangeHandler with store, and if defined, a base directory."""
    if not base_dir:
        base_dir = Path(__file__).parent / "resources" / "design_stages"
    service = FileSystemService(base_dir, "single_requirement")
    return ChangeHandler(service, store)


def test_new_remote_items(empty_local_store):
    """
    Given A filesystem service with design stages and an empty local store.

    When local and remote items are combined
    Then the output should have items in it.
    """
    handler = handler_with_single_requirement(empty_local_store)
    items = handler.combine_local_and_remote_items()
    assert items


def test_no_changes_to_items(qw_store_builder, test_design_stages):
    """
    Given A filesystem service with aRequirement and the same Requirement in the local store with no changes.

    When local and remote items are combined
    Then the output should have items in it.
    """
    # Arrange
    store = qw_store_builder(test_design_stages)
    handler = handler_with_single_requirement(store)
    # Act
    items = handler.combine_local_and_remote_items()
    assert items


def test_do_not_remove_local_item(
    mock_user_input,
    qw_store_builder,
    test_design_stages,
):
    """
    Given A filesystem service without design stages and a local store with a Requirement.

    When local and remote items are combined and the user does not want to delete the local stage
    Then the output should have items in it.
    """
    # Arrange
    store = qw_store_builder(test_design_stages)
    handler = handler_with_single_requirement(store, store._data_path)
    # Act
    mock_user_input(["n"])
    items = handler.combine_local_and_remote_items()

    assert items


def test_remove_local_item(
    mock_user_input,
    qw_store_builder,
    test_design_stages,
):
    """
    Given A filesystem service without design stages and a local store with a Requirement.

    When local and remote items are combined and the user wants to delete the local stage
    Then the output should have items in it.
    """
    # Arrange
    store = qw_store_builder(test_design_stages)
    handler = handler_with_single_requirement(store, store._data_path)
    # Act
    mock_user_input(["y"])
    items = handler.combine_local_and_remote_items()

    assert items == []


@pytest.mark.parametrize(
    ("response", "expected_title", "expected_version"),
    [
        ("n", "Old title", 1),
        ("u", "Calculate warfarin", 1),
        ("i", "Calculate warfarin", 2),
    ],
)
def test_same_items_with_changes(  # noqa: PLR0913 ignore too many functions to call
    mock_user_input,
    qw_store_builder,
    test_design_stages,
    response,
    expected_title,
    expected_version,
):
    """
    Given the same Requirement in the local and remote storage, but the local storage has a different title.

    When local and remote items are combined, and the user responds with a decision on updating
    Then the output stages should have the old title or new title, and increment the version as appropriate
    """
    # Arrange
    input_data = test_design_stages
    input_data[0]["title"] = "Old title"
    input_data[0]["description"] = (
        "Warfarin dose should be calculated based on patient age, gender and  weight.\n"
        "Some extra information..."
    )
    store = qw_store_builder(input_data)
    handler = handler_with_single_requirement(store)
    # Act
    mock_user_input([response])
    items = handler.combine_local_and_remote_items()

    assert items
    assert items[0].title == expected_title
    assert items[0].version == expected_version
