"""
The qw (Quality Workflow) tool helps enforce regulatory compliance
for projects managed on github.
"""

import json
import os
import sys
from enum import Enum
from typing import Annotated

import git
import github3
import keyring
import typer

app = typer.Typer()


class QwError(RuntimeError):
    pass


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


class GithubIssue(Issue):
    def __init__(self, issue) -> None:
        self.issue = issue

    def number(self) -> int:
        return self.issue.number

    def title(self) -> str:
        return self.issue.title


class Github(GitService):
    def __init__(self, conf):
        """Gets the gh auth token and logs into github with it."""
        super().__init__(conf)
        token = keyring.get_password("gh:github.com", "")
        self.gh = github3.login(token=token)

    def get_issue(self, number: int):
        issue = self.gh.issue(self.username, self.reponame, number)
        return GithubIssue(issue)


def get_service(conf: object = None) -> GitService:
    if conf is None:
        conf = get_configuration()
    name = conf.get("service", None)
    if name is None:
        msg = "Configuration is corrupt. Please run `qw init`"
        raise QwError(
            msg,
        )
    if name == str(Service.github):
        return Github(conf)
    msg = f"Do not know how to connect to the {name} service!"
    raise QwError(
        msg,
    )


@app.command()
def init(
    repo: Annotated[
        str | None,
        typer.Option(
            help="The URL (or remote name) for the repo containing the issues."
            + " If not supplied the remotes named 'upstream' and 'origin' will"
            + " be tried.",
        ),
    ] = None,
    service: Annotated[
        Service,
        typer.Option(
            help="Which service is hosting the issue tracker. Not required"
            + " if the repo URL begins 'github' or 'gitlab'.",
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            help="Replace any existing configuration.",
        ),
    ] = False,
) -> None:
    """Initializes this tool and the repository (as far as possible)."""
    git_dir = find_aunt_dir(".git")
    if not git_dir:
        msg = "We are not in a git project, so we cannot initialize!"
        raise QwError(
            msg,
        )
    base = os.path.dirname(git_dir)
    gitrepo = git.Repo(base)
    repo = get_repo_url(gitrepo, repo)
    qw_dir = os.path.join(base, ".qw")
    if os.path.isfile(qw_dir):
        msg = ".qw file exists, which is blocking us from making a .qw directory. Please delete it!"
        raise QwError(
            msg,
        )
    elif not os.path.isdir(qw_dir):
        os.mkdir(qw_dir)
    elif not force:
        msg = ".qw directory already exists! Use use existing configuration or use --force flag to reinitialize!"
        raise QwError(
            msg,
        )
    hur = remote_address_to_host_user_repo(repo)
    if hur is None:
        msg = f"'{repo}' does not seem to be a valid repo url!"
        raise QwError(
            msg,
        )
    host = hur[0]
    if service is None:
        service = hostname_to_service(host)
    if service is None:
        msg = f"'{host}' is not a service I know about!"
        raise QwError(
            msg,
        )
    conf = {
        "repo_url": repo,
        "repo_name": hur[2],
        "user_name": hur[1],
        "service": str(service),
    }
    conf_file_name = os.path.join(qw_dir, "conf.json")
    with open(conf_file_name, "w") as conf_file:
        json.dump(conf, conf_file, indent=2)


@app.command()
def check():
    """Checks whether all the traceability information is present."""
    conf = get_configuration()
    service = get_service(conf)
    print(conf)
    print(service.get_issue(1).title())


if __name__ == "__main__":
    try:
        app()
        sys.exit(0)
    except QwError as e:
        print(e)
        sys.exit(2)
