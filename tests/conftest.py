"""Fixtures used by across the entire test suite."""
from collections.abc import Callable

import pytest

from qw.local_store.main import LocalStore


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
