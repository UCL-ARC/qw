"""Fixtures used by across the entire test suite."""
import json
from collections.abc import Callable
from pathlib import Path

import pytest

from qw.design_stages.main import get_remote_stages
from qw.local_store.main import LocalStore
from qw.remote_repo.test_service import FileSystemService


@pytest.fixture()
def empty_local_store(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
) -> LocalStore:
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
    if hasattr(request, "param"):
        config_data.update(request.param)
    config_path = qw_dir / "conf.json"
    with config_path.open("w") as handler:
        json.dump(config_data, handler)

    return LocalStore(repo_dir)


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


@pytest.fixture()
def test_design_stages(request) -> list[dict]:
    """
    Read test resource in test resource directory.

    Useful for writing to tmp filesystem using qw_store_builder.

    :return: list of dicts, each representing a design stage
    """
    requirement_test_dir = (
        request.param if hasattr(request, "param") else "single_requirement"
    )
    service = FileSystemService(
        Path(__file__).parent / "resources" / "design_stages",
        requirement_test_dir,
    )
    stages = get_remote_stages(service)
    return [x.to_dict() for x in stages]
