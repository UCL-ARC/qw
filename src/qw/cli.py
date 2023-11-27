"""
The qw (Quality Workflow) tool.

Helps enforce regulatory compliance for projects managed on GitHub.
"""

import sys
from enum import Enum
import re
from typing import Annotated, Optional

import git
import typer
from loguru import logger
from rich.prompt import Prompt

from qw.base import QwError
from qw.changes import ChangeHandler
from qw.design_stages.main import (
    get_local_stages, UserNeed, Requirement
)
from qw.local_store.keyring import get_qw_password, set_qw_password
from qw.local_store.main import LocalStore
from qw.mergedoc import load_template
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


LOGLEVEL_TO_LOGURU = {
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
    logmodule: Annotated[
        list[str],
        typer.Option(
            help="Modules to log (default all)"
        ),
    ] = [],
):
    """
    Process global options.

    Processes the options passed before the command.
    """
    logger.remove()
    logfilter = {"": True}
    if len(logmodule) != 0:
        logfilter = {"": False}
        for lm in logmodule:
            logfilter[lm] = True
    logger.add(
        sys.stderr,
        level=LOGLEVEL_TO_LOGURU[loglevel],
        filter=logfilter,
    )


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

@app.command()
def generate_merge_fields(
    output: Annotated[
        str,
        typer.Option(
            help="Output file name",
        ),
    ] = "fields.csv"
):
    """
    Produce a file that can be imported into MS Word.

    In MS Word 2010 you choose "Select Recipients|Use Existing List..."
    from the "Mailings" ribbon, then choose this file. Now you can
    insert fields by clicking "Insert Merge Field" (still in the
    "Mailings" ribbon) and selecting the field you want.

    In LibreOffice you upload this file from the
    Insert|Field|More Fields... dialog, in the Database tab, with
    the "Mail merge fields" Type highlighted. You can add this file
    with the "Add database file" Browse... button. Open up the new
    item that appears and now you can highlight the field you want and
    click "Insert field". You can leave this dialog open and insert more
    fields as you edit the document.
    """
    headings = []
    examples = []
    for cls in [UserNeed, Requirement]:
        name = cls.design_stage.value
        fields = cls.base_fields | cls.not_required_fields
        for f in fields:
            field = f"{name}.{f}"
            headings.append(field)
            examples.append(f"<{field}>")
    with open(output, "wt") as out:
        out.write("\n".join([
            ",".join(line)
            for line in [headings, examples]
        ]))

@app.command()
def release():
    """Produce documentation by merging frozen values into templates."""
    data = get_merge_data()
    for (wt_path, wt_out) in store.release_word_templates():
        doc = load_template(wt_path)
        doc.write(output_file=wt_out, data=data)

def get_merge_data() -> dict[str, list[dict[str, any]]]:
    stages = get_local_stages(store)
    data = {}
    for s in stages:
        sd = s.to_dict()
        typ = sd['stage'].value
        if typ not in data:
            data[typ] = []
        data[typ].append(sd)
    return data


if __name__ == "__main__":
    try:
        app()
        sys.exit(0)
    except QwError as e:
        sys.stderr.write(str(e) + "\n")
        sys.exit(2)
