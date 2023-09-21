"""
Abstract Service (such as github or gitlab) in which
the project managment interest resides.
"""

from enum import Enum
import git
import json
import os

from qw.base import QwError

class Service(str, Enum):
    test = "test"
    github = "github"
    gitlab = "gitlab"


def find_aunt_dir(name: str) -> str:
    """
    Returns the directory with the required name in the closest
    ancestor of the current working directory, or None if there is no
    such directory (the daughter of an ancestor is a great^n aunt).
    """
    d = os.getcwd()
    while True:
        p = os.path.join(d, name)
        if os.path.isdir(p):
            return p
        (d, rej) = os.path.split(d)
        if rej == "":
            return None


def find_conf_dir() -> str:
    """Returns the .qw directory of the project we are in."""
    d = find_aunt_dir(".qw")
    if d is None:
        msg = (
            "Could not find a configuration directory, please initialize with `qw init`"
        )
        raise QwError(
            msg,
        )
    return d


def get_configuration() -> object:
    conf_file_name = os.path.join(find_conf_dir(), "conf.json")
    if not os.path.isfile(conf_file_name):
        msg = (
            "Could not find a configuration directory, please initialize with `qw init`"
        )
        raise QwError(
            msg,
        )
    with open(conf_file_name) as conf:
        return json.load(conf)


def get_repo_url(repo: git.Repo, name: str) -> str:
    """Finds the URL of the repo given the --repo=<> command-line option."""
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


def remote_address_to_host_user_repo(address: str) -> str:
    bits = address.split("://", 1)
    if len(bits) == 2:
        host_user_repo = bits[1].split("/", 2)
        if len(host_user_repo) != 3:
            return None
        (host, user, repo) = host_user_repo
    else:
        host_userrepo = address.split(":", 1)
        if len(host_userrepo) != 2:
            return None
        (host, userrepo) = host_userrepo
        user_repo = userrepo.split("/", 1)
        if len(user_repo) != 2:
            return None
        (user, repo) = user_repo
    uh = host.split("@", 1)
    if len(uh) == 2:
        host = uh[1]
    return (host, user, repo)


def hostname_to_service(hostname: str) -> str:
    if hostname.startswith("github."):
        return Service.github
    if hostname.startswith("gitlab."):
        return Service.gitlab
    return None


class Issue:
    def number(self) -> int:
        raise NotImplementedError

    def title(self) -> str:
        raise NotImplementedError


class GitService:
    def __init__(self, conf) -> None:
        self.conf = conf
        self.username = conf["user_name"]
        self.reponame = conf["repo_name"]

    def get_issue(self, number: int):
        """Gets the numbered issue."""
        raise NotImplementedError

