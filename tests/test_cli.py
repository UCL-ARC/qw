"""Test command line interface functionality."""
import pytest
from typer.testing import CliRunner

from qw.cli import app
from qw.local_store._repository import QwDirRequirementComponents

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
def mocked_store(monkeypatch, empty_local_store):
    """Set the qw local store to be the empty local store."""
    monkeypatch.setattr("qw.cli.store", empty_local_store)
    return empty_local_store


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


def test_configure_adds_templates(mocked_store):
    """
    Given no templates exist in git root (tmpdir).

    When `qw configure --workflow` is run
    Then templates should be copied and the cli should exit without error
    """
    result = runner.invoke(app, ["configure", "--workflow"])

    requirements_template = (
        mocked_store.base_dir / ".github" / "ISSUE_TEMPLATE" / "requirement.yml"
    )
    assert requirements_template.exists()
    assert "options:\n        - System" in requirements_template.read_text()
    assert (mocked_store.base_dir / ".github" / "PULL_REQUEST_TEMPLATE.md").exists()
    assert result.exit_code == 0


def test_configure_adds_requirement_components(mocked_store):
    """
    Given no templates exist in git root (tmpdir) and custom components with leading and trailing whitespace.

    When `qw configure --workflow` is run
    Then requirement template should have the component names in the dropdown, without the whitespace.
    """
    components_file = mocked_store.qw_dir / "components.csv"
    components_file.write_text(
        "name,short_code,description\n System ,X,Whole system requirements\n Fancy new component ,N,new requirements",
    )
    # re-initialise requirement component so it reads in new components file
    mocked_store._requirement_component = QwDirRequirementComponents(
        mocked_store.qw_dir,
    )

    result = runner.invoke(app, ["configure", "--workflow"])

    bullet_point = "        - "
    component_options = (
        f"options:\n{bullet_point}System\n{bullet_point}Fancy new component"
    )
    requirements_template = (
        mocked_store.base_dir / ".github" / "ISSUE_TEMPLATE" / "requirement.yml"
    )
    assert component_options in requirements_template.read_text()
    assert result.exit_code == 0


def test_configure_throws_if_templates_exist(mocked_store):
    """
    Given the pull request template exists already.

    When `qw configure` is run
    Then an exception should be thrown and the other templates should not exist
    """
    existing_file = (
        mocked_store.base_dir / ".github" / "ISSUE_TEMPLATE" / "requirement.yml"
    )
    existing_file.parent.mkdir(parents=True)
    existing_file.write_text("Now I exist.")

    result = runner.invoke(app, ["configure", "--workflow"])

    assert "Templates already exist" in " ".join(result.exception.args)
    assert str(existing_file) in " ".join(result.exception.args)
    assert result.exit_code != 0
    assert not (mocked_store.base_dir / ".github" / "PULL_REQUEST_TEMPLATE.md").exists()


def test_configure_force_templates_exist(mocked_store):
    """
    Given the pull request template exists already.

    When `qw configure --force --workflow` is run
    Then an exception should be thrown and the other templates should not exist
    """
    existing_file = (
        mocked_store.base_dir / ".github" / "ISSUE_TEMPLATE" / "requirement.yml"
    )
    existing_file.parent.mkdir(parents=True)
    existing_file.write_text("Now I exist.")

    result = runner.invoke(app, ["configure", "--force", "--workflow"])

    assert (mocked_store.base_dir / ".github" / "PULL_REQUEST_TEMPLATE.md").exists()
    assert result.exit_code == 0
