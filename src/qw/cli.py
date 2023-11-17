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
from qw.remote_repo.factory import get_service
from qw.remote_repo.service import (
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


LOGELEVEL_TO_LOGURU = {
    LogLevel.DEBUG: 10,
    LogLevel.INFO: 20,
    LogLevel.WARNING: 30,
    LogLevel.ERROR: 40,
}

store = LocalStore()


def _build_and_check_service():
    conf = store.read_configuration()
    service = get_service(conf)
    service.check()
    typer.echo("Can connect to the remote repository 🎉")
    return service


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
        logger.add(sys.stderr, level=LOGELEVEL_TO_LOGURU[loglevel])


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
    store.initialise_qw_files(repo, reponame, service, username)


@app.command()
def check(
    issue: Annotated[
        Optional[int],
        typer.Option(
            help="Issue number to check",
        ),
    ] = None,
    review_request: Annotated[
        Optional[int],
        typer.Option(
            help="Review request number to check",
        ),
    ] = None,
    token: Annotated[
        Optional[str],
        typer.Option(
            help="CI access token to use for checking, otherwise will use local config",
        ),
    ] = None,
    repository: Annotated[
        Optional[str],
        typer.Option(
            help="Repository in form '${organisation}/${repository}'",
        ),
    ] = None,
) -> None:
    """Check issue or pull request for any QW problems."""
    if token and repository:
        logger.info("Using CI access token for authorisation")
    else:
        logger.info(
            "Using local qw config for authorisation because '--token' and '--repository' were not used",
        )
        _build_and_check_service()
    # currently dummy function as doesn't need real functionality for configuration
    if issue and review_request:
        QwError(
            "Check should only be run on an issue or a review_request, not both at the same time",
        )
    if not (issue or review_request):
        QwError("Nothing given to check, please add a issue or review_request to check")
    logger.success(
        "Checks complete, stdout will contain a checklist of any problems found",
    )


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

    _build_and_check_service()


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
    service = _build_and_check_service()
    store.write_templates_and_ci(service, force=force)
    typer.echo(
        "Local repository updated, please commit the changes made to your local repository.",
    )
    service.update_remote(force=force)
    typer.echo(
        "Updated remote repository with rules",
    )


if __name__ == "__main__":
    try:
        app()
        sys.exit(0)
    except QwError as e:
        sys.stderr.write(str(e) + "\n")
        sys.exit(2)
