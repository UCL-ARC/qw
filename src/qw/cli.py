"""
The qw (Quality Workflow) tool helps enforce regulatory compliance
for projects managed on github.
"""

import json
import os
import sys
from typing import Annotated

import git
import typer
from loguru import logger

import qw.service
from qw.base import QwError

app = typer.Typer()


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
        qw.service.Service,
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
    git_dir = qw.service.find_aunt_dir(".git")
    if not git_dir:
        msg = "We are not in a git project, so we cannot initialize!"
        raise QwError(
            msg,
        )
    base = os.path.dirname(git_dir)
    gitrepo = git.Repo(base)
    repo = qw.service.get_repo_url(gitrepo, repo)
    qw_dir = os.path.join(base, ".qw")
    logger.info(
        ".qw directory is '{dir}'",
        dir=qw_dir,
    )
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
    hur = qw.service.remote_address_to_host_user_repo(repo)
    if hur is None:
        msg = f"'{repo}' does not seem to be a valid repo url!"
        raise QwError(
            msg,
        )
    host = hur[0]
    if service is None:
        service = qw.service.hostname_to_service(host)
    if service is None:
        msg = f"'{host}' is not a service I know about!"
        raise QwError(
            msg,
        )
    logger.info(
        "service, owner, repo: {service}, {owner}, {repo}",
        service=str(service),
        owner=hur[1],
        repo=hur[2],
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
    conf = qw.service.get_configuration()
    service = qw.service.get_service(conf)
    print(conf)
    print(service.get_issue(1).title())


if __name__ == "__main__":
    try:
        app()
        sys.exit(0)
    except QwError as e:
        print(e)
        sys.exit(2)
