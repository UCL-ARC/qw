"""
Abstract git hosting service.

Abstract Service (such as github or gitlab) in which
the project managment interest resides.
"""

import re
from abc import ABC, abstractmethod
from collections.abc import Iterable
from enum import Enum
from pathlib import Path

import git

from qw.base import QwError
from qw.design_stages.categories import RemoteItemType


class Service(str, Enum):
    """Git hosting service identifiers."""

    TEST = "test"
    GITHUB = "github"
    GITLAB = "gitlab"


def get_repo_url(repo: git.Repo, name: str) -> str:
    """
    Get the repo URL.

    Find the URL of the repo given the --repo=<> command-line
    option and the git remotes configured.
    """
    if name is None:
        for remote_name in ["upstream", "origin"]:
            if remote_name in repo.remotes:
                return repo.remotes[remote_name].url
        msg = "No repo name supplied, and no remote called upstream or origin."
        raise QwError(
            msg,
        )
    if name in repo.remotes:
        return repo.remotes[name].url
    for remote in repo.remotes:
        if remote.url == repo:
            return repo
    msg = f"The supplied repo '{repo}' is neither the name or url of a known remote."
    raise QwError(
        msg,
    )


def splitstr(string, sep, count) -> tuple | None:
    """
    Split like str.split().

    Returns none if `count` components were not found
    """
    r = string.split(sep, count - 1)
    if len(r) == count:
        return r
    return None


def remote_address_to_host_user_repo(
    address: str,
) -> tuple[str, str, str]:
    """
    Get (host, user, reponame) triple from the remote address.

    Takes the remote URL (such as git@github.com:me/my_repo.git)
    and returns the interesting components of it
    (such as ("github.com", "me", "my_repo")).
    """
    bits = splitstr(address, "://", 2)
    if bits is not None:
        host_user_repo = splitstr(bits[1], "/", 3)
        if host_user_repo is None:
            msg = f"Your remote address ({bits[1]}) must be user/repo"
            raise QwError(msg)
        (host, user, repo_raw) = host_user_repo
    else:
        host_userrepo = splitstr(address, ":", 2)
        if host_userrepo is None:
            msg = (
                f"Your remote address ({address}) must have a protocol"
                " (such as https://) or be of the form host:user/repo."
            )
            raise QwError(msg)
        (host, userrepo) = host_userrepo
        user_repo = splitstr(userrepo, "/", 2)
        if user_repo is None:
            msg = (
                f"Your remote address ({address}) must have a protocol"
                " (such as https://) or be of the form host:user/repo."
            )
            raise QwError(msg)
        (user, repo_raw) = user_repo
    uh = splitstr(host, "@", 2)
    if uh is not None:
        host = uh[1]
    repo = re.sub(r"\.git$", "", repo_raw)
    return (host, user, repo)


def hostname_to_service(hostname: str) -> str:
    """
    Guesses the service type from the host name.

    From a hostname (such as gitlab.mydomain.com)
    returns the service it looks like. Raises an
    exception if it cannot work it out (in which)
    case the user should specify it explicitly.
    """
    if hostname.startswith("github."):
        return Service.GITHUB
    if hostname.startswith("gitlab."):
        return Service.GITLAB
    msg = f"'{hostname}' is not a service I know about!"
    raise QwError(
        msg,
    )


class Issue(ABC):
    """
    Project management Issue.

    For example a bug report, user need, or requirement.
    """

    @property
    @abstractmethod
    def number(self) -> int:
        """
        Get issue number.

        The identifying number that the users associate with this
        issue.
        """
        ...

    @property
    @abstractmethod
    def title(self) -> str:
        """
        Get title.

        The title of the issue, such as is visible in issue lists.
        """
        ...

    @property
    @abstractmethod
    def labels(self) -> list[str]:
        """Get the label names for the issue."""
        ...

    @property
    @abstractmethod
    def body(self) -> str:
        r"""Get the body of the first comment, always using `\n` as the newline character."""
        ...

    @property
    @abstractmethod
    def item_type(self) -> RemoteItemType:
        """Get the type of the issue, as we may handle a pull request differently to an issue."""
        ...


class PullRequest(Issue):
    """Pull Request."""

    @property
    @abstractmethod
    def closing_issues(self) -> list[int]:
        """
        Get the list of ID numbers of closing issues for this issue.

        Only makes sense for Pull Requests; that is, Issues that return
        REQUEST from their item_type method.
        """
        ...


class GitService(ABC):
    """A service hosting a git repository and project management tools."""

    def __init__(self, conf) -> None:
        """Initialize a service with configuration."""
        self.conf = conf
        self.username = conf["user_name"]
        self.reponame = conf["repo_name"]
        self.qw_resources = Path(__file__).parents[2] / "resources"

    @abstractmethod
    def get_issue(self, number: int) -> Issue:
        """Get the numbered issue."""
        ...

    @property
    @abstractmethod
    def issues(self) -> list[Issue]:
        """Get all issues for the repository."""
        ...

    @property
    @abstractmethod
    def pull_requests(self) -> list[Issue]:
        """Get all pull requests for the repository."""
        ...

    @property
    @abstractmethod
    def template_paths(self) -> Iterable[Path]:
        """Paths for templates to copy to the service."""
        ...

    def relative_target_path(self, base_folder: str, resource_path: Path) -> Path:
        """Find the relative path that a resource should be copied to."""
        return resource_path.relative_to(self.qw_resources / base_folder)

    @abstractmethod
    def update_remote(self, *, force: bool) -> None:
        """Update remote repository with configration for qw tool."""

    @abstractmethod
    def check(self) -> bool:
        """Check the connection to the service."""
