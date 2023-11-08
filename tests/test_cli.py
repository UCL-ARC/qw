"""Test command line interface functionality."""
import pytest
from typer.testing import CliRunner

from qw.cli import app

runner = CliRunner()


@pytest.fixture()
def mock_keyvault_with_value(monkeypatch):
    """Mock keyvault, so that we don't alter the real one, and return an acceptable value."""

    def _take_input(responses: list[str]):
        values = iter(responses)
        monkeypatch.setattr(
            "keyring.get_password",
            lambda service_name, username: next(values),  # noqa: ARG005
        )
        monkeypatch.setattr(
            "keyring.set_password",
            lambda service_name, username, password: None,  # noqa: ARG005
        )

    return _take_input


@pytest.fixture(autouse=True)
def _local_store(monkeypatch, empty_local_store):
    """Set the qw local store to be the empty local store."""
    monkeypatch.setattr("qw.cli.store", empty_local_store)


def test_login_success(mock_user_input, mock_keyvault_with_value):
    """
    Given no password exists in the mocked store.

    When login is run with a password entered
    Then the application should be able to connect to the local store
    """
    pw = "I'm a test password"
    mock_keyvault_with_value([None, pw])
    mock_user_input([pw])

    result = runner.invoke(app, ["login"])

    assert "Can connect" in result.stdout
    assert result.exit_code == 0


def test_login_pat_exists(mock_user_input, mock_keyvault_with_value):
    """
    Given password already exists in the mocked store.

    When login is run without a `--force` flag
    Then this should be reported without being overriden
    """
    pw = "I'm a test password"
    mock_keyvault_with_value([pw])
    mock_user_input([pw])

    result = runner.invoke(app, ["login"])

    assert "Access token already exists" in result.stdout
    assert result.exit_code == 0


def test_login_force(mock_user_input, mock_keyvault_with_value):
    """
    Given password already exists in the mocked store.

    When login is run with a `--force` flag
    Then the application should be able to connect to the local store
    """
    pw = "I'm a test password"
    mock_keyvault_with_value([pw, pw])
    mock_user_input([pw])

    result = runner.invoke(app, ["login", "--force"])

    assert "Can connect" in result.stdout
    assert result.exit_code == 0


def test_login_whitespace_password(mock_user_input, mock_keyvault_with_value):
    """
    Given no password exists in mocked keychain.

    When a whitespace password is entered
    Then an exception should be thrown
    """
    pw_input = "  "
    mock_keyvault_with_value([None])
    mock_user_input([pw_input])

    result = runner.invoke(app, ["login"])

    assert "Access token was empty" in " ".join(result.exception.args)
    assert result.exit_code != 0
