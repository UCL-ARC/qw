"""Testing of common service functions."""
import pytest

from qw.remote_repo.service import remote_address_to_host_user_repo


@pytest.mark.parametrize(
    "address",
    [
        "git@github.com:organisation/repo.git",
        "https://github.com/organisation/repo.git",
    ],
)
def test_remote_address_to_host_user_repo_successful(address):
    """
    Test remote is parsed correctly.

    Given GitHub addresses for repos in ssh and https format
    When these are parsed by our service logic
    Then the host, organisation and repo should match.
    """
    host, org, repo = remote_address_to_host_user_repo(address)
    assert host == "github.com"
    assert org == "organisation"
    assert repo == "repo"
