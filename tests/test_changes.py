"""Test for changes."""
from collections.abc import Callable
from pathlib import Path

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
    # Currently no conf.json created, but could create a config if we required i

    return store


@pytest.fixture()
def qw_store_builder(empty_local_store) -> Callable[[list[dict]], LocalStore]:
    """Write data to temporary qw local store."""

    def _add_to_store(data) -> LocalStore:
        empty_local_store.write_local_data(data)
        return empty_local_store

    return _add_to_store


@pytest.fixture()
def qw_test_stages_from_resources() -> list[dict]:
    """
    Read test resources in design stages and returns data as list of dicts.

     Useful for writing to tmp filesystem using qw_store_builder.
    """
    service = FileSystemService()
    stages = get_remote_stages(service)
    return [x.to_dict() for x in stages]


@pytest.fixture()
def handler_builder() -> Callable[[LocalStore, Path | None], ChangeHandler]:
    """Build ChangeHandler with store, and if defined, a base directory."""

    def _config_handler(store, base_dir=None) -> ChangeHandler:
        service = FileSystemService(base_dir)
        return ChangeHandler(service, store)

    return _config_handler


def test_new_remote_items(handler_builder, empty_local_store):
    """
    Given A filesystem service with design stages and an empty local store.

    When local and remote items are combined
    Then the output should have items in it.
    """
    handler = handler_builder(empty_local_store)
    items = handler.combine_local_and_remote_items()
    assert items


def test_no_changes_to_items(
    handler_builder,
    qw_store_builder,
    qw_test_stages_from_resources,
):
    """
    Given A filesystem service with design stages and the same items in the local store with no changes.

    When local and remote items are combined
    Then the output should have items in it.
    """
    # Arrange
    store = qw_store_builder(qw_test_stages_from_resources)
    handler = handler_builder(store)
    # Act
    items = handler.combine_local_and_remote_items()
    assert items


def test_no_remote_items_with_local(
    handler_builder,
    qw_store_builder,
    qw_test_stages_from_resources,
):
    """
    Given A filesystem service without design stages and a local store with design stages.

    When local and remote items are combined
    Then the output should have items in it.
    """
    # Arrange
    store = qw_store_builder(qw_test_stages_from_resources)
    handler = handler_builder(store, store._data_path)
    # Act
    items = handler.combine_local_and_remote_items()

    assert items


def test_same_items_with_changes(
    handler_builder,
    qw_store_builder,
    qw_test_stages_from_resources,
):
    """
    Given the same stages in the local and remote storage, but the local storage has a different title.

    When local and remote items are combined
    Then the output shouldn't have items in it, until we do prompting and then we can ensure that.
    """
    # Arrange
    input_data = qw_test_stages_from_resources
    input_data[0]["title"] = "Old title"
    store = qw_store_builder(input_data)
    handler = handler_builder(store)
    # Act
    items = handler.combine_local_and_remote_items()

    assert items == []
