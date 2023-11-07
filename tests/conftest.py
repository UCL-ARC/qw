"""Fixtures used by across the entire test suite."""
import json
from collections.abc import Callable
from pathlib import Path

import pytest

from qw.local_store.main import LocalStore


@pytest.fixture()
def empty_local_store(tmp_path_factory: pytest.TempPathFactory) -> LocalStore:
    """Create tmp dir with .qw child dir, returning a local store instance."""
    repo_dir = tmp_path_factory.mktemp("fake_repo")
    store = LocalStore(repo_dir)
    qw_dir = store.get_or_create_qw_dir()
    config_data = {
        "repo_url": "git@github.com:local/repo.git",
        "repo_name": "repo",
        "user_name": "local",
        "service": "Service.TEST",
        "resource_base": str(Path(__file__).parent / "resources" / "design_stages"),
    }
    config_path = qw_dir / "conf.json"
    with config_path.open("w") as handler:
        json.dump(config_data, handler)

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
def mock_user_input(monkeypatch):
    """Mock user input from prompt, uses internal method to be able to take in arguments."""

    def _take_input(responses: list[str]):
        answers = iter(responses)
        monkeypatch.setattr("builtins.input", lambda: next(answers))

    return _take_input
