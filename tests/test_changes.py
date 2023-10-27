"""Test for changes."""
from collections.abc import Callable

import pytest

from qw.changes import ChangeHandler
from qw.design_stages.main import get_remote_stages
from qw.local_store.main import LocalStore
from tests.helpers.mock_service import FileSystemService


@pytest.fixture()
def empty_local_store(tmp_path_factory: pytest.TempPathFactory) -> LocalStore:
    """Create tmp dir with .qw child dir, returning a local store instance."""
    repo_dir = tmp_path_factory.mktemp("fake_repo")
    store = LocalStore(repo_dir)
    store.get_or_create_qw_dir()
    # Currently no conf.json created, but could create a config if we required it

    return store


@pytest.fixture()
def qw_store_builder(empty_local_store) -> Callable[[list[dict]], LocalStore]:
    """
    Write data to temporary qw local store.

    Returns internal function that we can take in data and add to an existing fixture.
    """

    def _add_to_store(data) -> LocalStore:
        empty_local_store.write_local_data(data)
        return empty_local_store

    return _add_to_store


@pytest.fixture()
def single_requirement() -> list[dict]:
    """
    Read test resource in single_requirement and returns data as list of the single dict.

     Useful for writing to tmp filesystem using qw_store_builder.
    """
    service = FileSystemService("single_requirement")
    stages = get_remote_stages(service)
    return [x.to_dict() for x in stages]


@pytest.fixture()
def mock_user_input(monkeypatch):
    """Mock user input from prompt, uses internal method to be able to take in arguments."""

    def _take_input(responses: list[str]):
        answers = iter(responses)
        monkeypatch.setattr("builtins.input", lambda: next(answers))

    return _take_input


def handler_with_single_requirement(store, base_dir=None) -> ChangeHandler:
    """Build ChangeHandler with store, and if defined, a base directory."""
    service = FileSystemService("single_requirement", base_dir)
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


def test_no_changes_to_items(qw_store_builder, single_requirement):
    """
    Given A filesystem service with aRequirement and the same Requirement in the local store with no changes.

    When local and remote items are combined
    Then the output should have items in it.
    """
    # Arrange
    store = qw_store_builder(single_requirement)
    handler = handler_with_single_requirement(store)
    # Act
    items = handler.combine_local_and_remote_items()
    assert items


def test_do_not_remove_local_item(
    mock_user_input,
    qw_store_builder,
    single_requirement,
):
    """
    Given A filesystem service without design stages and a local store with a Requirement.

    When local and remote items are combined and the user does not want to delete the local stage
    Then the output should have items in it.
    """
    # Arrange
    store = qw_store_builder(single_requirement)
    handler = handler_with_single_requirement(store, store._data_path)
    # Act
    mock_user_input(["n"])
    items = handler.combine_local_and_remote_items()

    assert items


def test_remove_local_item(
    mock_user_input,
    qw_store_builder,
    single_requirement,
):
    """
    Given A filesystem service without design stages and a local store with a Requirement.

    When local and remote items are combined and the user wants to delete the local stage
    Then the output should have items in it.
    """
    # Arrange
    store = qw_store_builder(single_requirement)
    handler = handler_with_single_requirement(store, store._data_path)
    # Act
    mock_user_input(["y"])
    items = handler.combine_local_and_remote_items()

    assert items == []


@pytest.mark.parametrize(
    ("response", "expected_title"),
    [
        ("Nothing", "Old title"),
        ("Update without version increment", "Calculate warfarin"),
        ("Update and increment version", "Calculate warfarin"),
    ],
)
def test_same_items_with_changes(
    mock_user_input,
    qw_store_builder,
    single_requirement,
    response,
    expected_title,
):
    """
    Given the same Requirement in the local and remote storage, but the local storage has a different title.

    When local and remote items are combined, and the user responds with a decision on updating
    Then the output stages should have the old title or new title as appropriate
    """
    # Arrange
    input_data = single_requirement
    input_data[0]["title"] = "Old title"
    store = qw_store_builder(input_data)
    handler = handler_with_single_requirement(store)
    # Act
    mock_user_input([response])
    items = handler.combine_local_and_remote_items()

    assert items
    assert items[0].title == expected_title
