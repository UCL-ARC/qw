"""
The qw (Quality Workflow) tool.

Helps enforce regulatory compliance for projects managed on GitHub.
"""

import sys
from enum import Enum
from typing import Annotated, Optional

import git
import typer
from loguru import logger
from rich.prompt import Prompt

from qw.base import QwError
from qw.changes import ChangeHandler
from qw.local_store.keyring import get_qw_password, set_qw_password
from qw.local_store.main import LocalStore
from qw.mergedoc import load_template
from qw.remote_repo.factory import get_service
from qw.remote_repo.service import (
    GitService,
    Service,
    get_repo_url,
    hostname_to_service,
    remote_address_to_host_user_repo,
)

app = typer.Typer()


class LogLevel(str, Enum):
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

store = LocalStore()


@app.callback()
def main(
    loglevel: Annotated[
        Optional[LogLevel],
        typer.Option(
            help="Level of logging to output",
        ),
    ] = LogLevel.INFO,
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
        Optional[Service],
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
    gitrepo = git.Repo(store.base_dir)
    repo = get_repo_url(gitrepo, repo)
    store.get_or_create_qw_dir(force=force)
    (host, username, reponame) = remote_address_to_host_user_repo(repo)
    if service is None:
        service = hostname_to_service(host)
    store.write_to_config(repo, reponame, service, username)


@app.command()
def check() -> GitService:
    """Check that qw can connect to the remote repository."""
    conf = store.read_configuration()
    service = get_service(conf)

    service.check()
    typer.echo("Can connect to the remote repository 🎉")
    return service


@app.command()
def login(
    *,
    force: Annotated[
        Optional[bool],
        typer.Option(
            help="Replace existing access credentials.",
        ),
    ] = False,
):
    """Add access credentials for the remote repository."""
    conf = store.read_configuration()
    existing_access_token = get_qw_password(conf["user_name"], conf["repo_name"])

    if existing_access_token and not force:
        typer.echo(
            "Access token already exists, rerun with '--force' if you want to override it.",
        )
    else:
        access_token = Prompt.ask(
            f"Please copy the access token for {conf['service']}",
        )

        set_qw_password(conf["user_name"], conf["repo_name"], access_token)

    check()


@app.command()
def freeze():
    """Freeze the state of remote design stages and update local store."""
    conf = store.read_configuration()
    service = get_service(conf)
    change_handler = ChangeHandler(service, store)
    to_save = change_handler.combine_local_and_remote_items()
    store.write_local_data([x.to_dict() for x in to_save])
    logger.info("Finished freeze")


@app.command()
def configure(
    force: Annotated[
        Optional[bool],
        typer.Option(
            help="Replace existing configuration.",
        ),
    ] = False,
):
    """Configure remote repository for qw (after initialisation and login credentials added)."""
    service = check()
    store.write_templates(service, force=force)


@app.command()
def release():
    """Produce documentation by merging frozen values into templates."""
    with load_template("tests/resources/msword/test_template.docx") as doc:
        doc.write(
            outputFile="out.docx",
            data={
                "soup": [{
                    "id": "34",
                    "name": "Python",
                    "description": "The **Python** programming language"
                }, {
                    "id": "75",
                    "name": "python-docx",
                    "description": "The *Python* module `python-docx`.\n* provides access to MS Word Documents\n* Isn't very good"
                }],
                "software-requirement": [{
                    "id": "101",
                    "name": "Dose input",
                    "description": "Allow the user to input the *dose*.",
                    "system-requirement": "31"
                }, {
                    "id": "102",
                    "name": "Dose measurement",
                    "description": "The *hardware* must measure the dose given.",
                    "system-requirement": "32",
                }, {
                    "id": "103",
                    "name": "Dose articulation",
                    "description": "The *hardware* must stop delivering the medicine when dose given meets the dose required.",
                    "system-requirement": "32",
                }, {
                    "id": "104",
                    "name": "Lock screen",
                    "description": "The [screen](https://dictionary.cambridge.org/dictionary/english/screen) should show `locked` when the _lock_ button is pressed",
                    "system-requirement": "33"
                }],
                "system-requirement": [{
                    "id": "31",
                    "name": "Dose input",
                    "description": "User must be able to input the dose"
                }, {
                    "id": "32",
                    "name": "Dose correct",
                    "description": "Dose must match the input dose"
                }, {
                    "id": "33",
                    "name": "Lockable",
                    "description": "Device should be easily lockable and only unlockable by the registered user."
                }, {
                    "id": "34",
                    "name": "Something else",
                    "description": "Are we having **fun** yet?"
                }]
            }
        )


if __name__ == "__main__":
    try:
        app()
        sys.exit(0)
    except QwError as e:
        sys.stderr.write(str(e) + "\n")
        sys.exit(2)
