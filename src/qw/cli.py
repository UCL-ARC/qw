"""
The qw (Quality Workflow) tool.

Helps enforce regulatory compliance for projects managed on github.
"""

import json
import sys
from enum import Enum
from typing import Annotated, Optional

import git
import typer
from loguru import logger

import qw.factory
import qw.service
from qw.base import QwError
import qw.mergedoc

app = typer.Typer()


class LogLevel(Enum):
    """Log Level."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


LOGLEVEL_TO_LOGURU = {
    LogLevel.DEBUG: 10,
    LogLevel.INFO: 20,
    LogLevel.WARNING: 30,
    LogLevel.ERROR: 40,
}


@app.callback()
def main(
    loglevel: Annotated[
        Optional[LogLevel],
        typer.Option(
            help="Level of logging to output",
        ),
    ] = None,
):
    """
    Process global options.

    Processes the options passed before the command.
    """
    logger.remove()
    if loglevel is not None:
        logger.add(sys.stderr, level=LOGLEVEL_TO_LOGURU[loglevel])


@app.command()
def init(
    repo: Annotated[
        Optional[str],
        typer.Option(
            help="The URL (or remote name) for the repo containing"
            " the issues. If not supplied the remotes named"
            " 'upstream' and 'origin' will be tried.",
        ),
    ] = None,
    service: Annotated[
        Optional[qw.service.Service],
        typer.Option(
            help="Which service is hosting the issue tracker. Not"
            " required if the repo URL begins 'github' or 'gitlab'.",
        ),
    ] = None,
    force: Annotated[
        Optional[bool],
        typer.Option(
            help="Replace any existing configuration.",
        ),
    ] = False,
) -> None:
    """Initialize this tool and the repository (as far as possible)."""
    git_dir = qw.service.find_aunt_dir(
        ".git",
        "We are not in a git project, so we cannot initialize!",
    )
    base = git_dir.parent
    gitrepo = git.Repo(base)
    repo = qw.service.get_repo_url(gitrepo, repo)
    qw_dir = base / ".qw"
    logger.debug(
        ".qw directory is '{dir}'",
        dir=qw_dir,
    )
    if qw_dir.is_file():
        msg = (
            ".qw file exists, which is blocking us from making"
            " a .qw directory. Please delete it!"
        )
        raise QwError(
            msg,
        )
    if not qw_dir.is_dir():
        qw_dir.mkdir()
    elif not force:
        msg = (
            ".qw directory already exists! Use existing"
            " configuration or use --force flag to reinitialize!"
        )
        raise QwError(
            msg,
        )
    (host, username, reponame) = qw.service.remote_address_to_host_user_repo(repo)
    if service is None:
        service = qw.service.hostname_to_service(host)
    logger.debug(
        "service, owner, repo: {service}, {owner}, {repo}",
        service=str(service),
        owner=username,
        repo=reponame,
    )
    conf = {
        "repo_url": repo,
        "repo_name": reponame,
        "user_name": username,
        "service": str(service),
    }
    conf_file_name = qw_dir / "conf.json"
    with conf_file_name.open("w") as conf_file:
        json.dump(conf, conf_file, indent=2)


@app.command()
def check():
    """Check whether all the traceability information is present."""
    conf = qw.service.get_configuration()
    service = qw.factory.get_service(conf)
    sys.stdout.write(str(conf))
    sys.stdout.write(service.get_issue(1).title())


@app.command()
def release():
    """Produce documentation by merging frozen values into templates."""
    with qw.mergedoc.load_template("tests/resources/msword/test_template.docx") as doc:
        doc.write(
            outputFile="out.docx",
            simple={
                "system-requirement-description": "a description for you"
            },
            tables=[[{
                "system-requirement-id": "1",
                "system-requirement-name": "one"
            },{
                "system-requirement-id": "3",
                "system-requirement-name": "three"
            },{
                "system-requirement-id": "5",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "7",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "9",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "6",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "4",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "2",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "0",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "8",
                "system-requirement-name": "five"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "64",
                "system-requirement-name": "sixty-four"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "64",
                "system-requirement-name": "sixty-four"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "64",
                "system-requirement-name": "sixty-four"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "64",
                "system-requirement-name": "sixty-four"
            },{
                "system-requirement-id": "128",
                "system-requirement-name": "one hundred and twenty-eight"
            },{
                "system-requirement-id": "72",
                "system-requirement-name": "seventy-two"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "64",
                "system-requirement-name": "sixty-four"
            },{
                "system-requirement-id": "128",
                "system-requirement-name": "one hundred and twenty-eight"
            },{
                "system-requirement-id": "72",
                "system-requirement-name": "seventy-two"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "64",
                "system-requirement-name": "sixty-four"
            },{
                "system-requirement-id": "128",
                "system-requirement-name": "one hundred and twenty-eight"
            },{
                "system-requirement-id": "72",
                "system-requirement-name": "seventy-two"
            },{
                "system-requirement-id": "50",
                "system-requirement-name": "fifty"
            },{
                "system-requirement-id": "64",
                "system-requirement-name": "sixty-four"
            },{
                "system-requirement-id": "128",
                "system-requirement-name": "one hundred and twenty-eight"
            },{
                "system-requirement-id": "72",
                "system-requirement-name": "seventy-two"
            }]]
        )


if __name__ == "__main__":
    try:
        app()
        sys.exit(0)
    except QwError as e:
        sys.stderr.write(str(e) + "\n")
        sys.exit(2)
