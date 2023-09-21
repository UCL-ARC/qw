"""
Abstract git hosting service.

Abstract Service (such as github or gitlab) in which
the project managment interest resides.
"""

import json
import pathlib
from enum import Enum

import git

from qw.base import QwError


class Service(str, Enum):
    """Git hosting service identifiers."""

    TEST = "test"
    GITHUB = "github"
    GITLAB = "gitlab"


def find_aunt_dir(name: str, error_msg: str) -> pathlib.Path:
    """
    Find a directory within this or some ancestor directory.

    Returns the directory with the required name in the closest
    ancestor of the current working directory, or None if there is no
    such directory (the daughter of an ancestor is a great^n aunt).
    """
    d = pathlib.Path.cwd()
    while True:
        p = d / name
        if p.is_dir():
            return p
        if d.name == "":
            raise QwError(
                error_msg,
            )
        d = d.parent


def find_conf_dir() -> pathlib.Path:
    """Return the .qw directory of the project we are in."""
    return find_aunt_dir(
        ".qw",
        "Could not find a configuration directory, please initialize with `qw init`",
    )


def get_configuration() -> dict:
    """Get the configuration (as a dict) from the .qw/conf.json file."""
    conf_file_name = find_conf_dir() / "conf.json"
    if not conf_file_name.is_file():
        msg = (
            "Could not find a configuration directory, please"
            " initialize with `qw init`"
        )
        raise QwError(
            msg,
        )
    with conf_file_name.open() as conf:
        return json.load(conf)


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
) -> tuple[str, str, str] | None:
    """
    Get (host, user, reponame) triple from the remote address.

    Takes the remote URL (such as git@github.com:me/my_repo)
    and returns the interesting components of it
    (such as ("github.com", "me", "my_repo")).
    """
    bits = splitstr(address, "://", 2)
    if bits is not None:
        host_user_repo = splitstr(bits[1], "/", 3)
        if host_user_repo is None:
            return None
        (host, user, repo) = host_user_repo
    else:
        host_userrepo = splitstr(address, ":", 2)
        if host_userrepo is None:
            return None
        (host, userrepo) = host_userrepo
        user_repo = splitstr(userrepo, "/", 2)
        if user_repo is None:
            return None
        (user, repo) = user_repo
    uh = splitstr(host, "@", 2)
    if uh is not None:
        host = uh[1]
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


class Issue:
    """
    Project management Issue.

    For example a bug report, user need, or
    design input.
    """

    def number(self) -> int:
        """
        Get issue number.

        The identifying number that the users associate with this
        issue.
        """
        raise NotImplementedError

    def title(self) -> str:
        """
        Get title.

        The title of the issue, such as is visible in issue lists.
        """
        raise NotImplementedError


class GitService:
    """A service hosting a git repository and project management tools."""

    def __init__(self, conf) -> None:
        """Initialize a service with configuration."""
        self.conf = conf
        self.username = conf["user_name"]
        self.reponame = conf["repo_name"]

    def get_issue(self, number: int):
        """Get the numbered issue."""
        raise NotImplementedError
