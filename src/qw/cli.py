"""
The qw (Quality Workflow) tool.

Helps enforce regulatory compliance for projects managed on GitHub.
"""

import sys
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Optional

import git
import typer
from loguru import logger
from rich.prompt import Prompt

from qw.base import QwError
from qw.changes import ChangeHandler
from qw.design_stages.checks import run_checks
from qw.design_stages.main import (
    DESIGN_STAGE_CLASSES,
    get_design_stage_class_from_name,
    get_local_stages,
    get_remote_stages,
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


def _build_and_check_service(conf: dict | None = None):
    if conf is None:
        conf = store.read_configuration()
    service = get_service(conf)
    service.check()
    typer.echo("Can connect to the remote repository 🎉")
    return service


@app.callback()
def main(
    loglevel: Annotated[
        LogLevel,
        typer.Option(
            help="Level of logging to output",
        ),
    ] = LogLevel.INFO,
    logmodule: Annotated[
        list[str],
        typer.Option(
            help="Modules to log (default all)",
        ),
        # In order to pass all ruff, mypy and black,
        # we need a default, we need it to match the annotation,
        # we need the annotation not to be list[str] | None, we
        # need it not to be a mutable object. There is nothing
        # that matches all four, so we use []. typer will use
        # this if no --logmodule option is given, but we are not
        # changing it and this function is only called once, so
        # it does not really matter.
    ] = [],  # noqa: B006
):
    """
    Process global options.

    Processes the options passed before the command.
    """
    logger.remove()
    logfilter = {"": True}
    if logmodule is not None and len(logmodule) != 0:
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
            help="Issue number to check (default is all of them)",
            show_default=False,
        ),
    ] = None,
    review_request: Annotated[
        Optional[int],
        typer.Option(
            help="Review request number to check (default is all of them)",
            show_default=False,
        ),
    ] = None,
    token: Annotated[
        Optional[str],
        typer.Option(
            help=(
                "CI access token to use for checking, if not run from a"
                " git repository."
            ),
            show_default=False,
        ),
    ] = None,
    repository: Annotated[
        Optional[str],
        typer.Option(
            help=(
                "Repository URL (like https://github.com/me/repo or"
                " github.com:me/repo) if not run from a git repository."
            ),
            show_default=False,
        ),
    ] = None,
    remote: Annotated[
        bool,
        typer.Option(
            "--remote/--local",
            help=(
                "Use remote repository or local store (default is --remote"
                " if --repository is supplied or --local otherwise)"
            ),
            show_default=False,
        ),
    ] = False,
) -> None:
    """Check issue or pull request for any QW problems."""
    kwargs = {}
    if token and repository:
        logger.info("Using CI access token for authorisation")
        (host, username, reponame) = remote_address_to_host_user_repo(repository)
        servicename = hostname_to_service(host)
        service = _build_and_check_service(
            {
                "user_name": username,
                "repo_name": reponame,
                "service": servicename,
                "token": token,
            },
        )
        stages = get_remote_stages(service)
    elif remote:
        service = _build_and_check_service()
        stages = get_remote_stages(service)
    else:
        logger.info("Using local qw config for authorisation.")
        stages = get_local_stages(store)
    # currently dummy function as doesn't need real functionality for configuration
    if issue and review_request:
        QwError(
            "Check should only be run on an issue or a review_request, not both at the same time",
        )
    if not (issue or review_request):
        QwError("Nothing given to check, please add a issue or review_request to check")
    if issue is not None:
        kwargs["issues"] = {issue}
    if review_request is not None:
        kwargs["prs"] = {review_request}
    result = run_checks(stages, **kwargs)
    if result.failures:
        logger.error(
            "Ran {} check(s) over {} object(s)",
            result.check_count,
            result.object_count,
        )
        logger.error("Some checks failed:")
        for failure in result.failures:
            logger.error(failure)
        typer.Exit(code=1)
    else:
        logger.success(
            "OK: Ran {} check(s) over {} object(s), all successful",
            result.check_count,
            result.object_count,
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
def freeze(
    dry_run: Annotated[
        Optional[bool],
        typer.Option(
            "--dry-run",
            "-n",
            help="Report differences but do not store the results.",
        ),
    ] = False,
):
    """Freeze the state of remote design stages and update local store."""
    conf = store.read_configuration()
    service = get_service(conf)
    change_handler = ChangeHandler(service, store)
    diff_elements = change_handler.diff_remote_and_local_items()
    if dry_run:
        logger.info("Finished freeze (dry run)")
    else:
        to_save = change_handler.get_local_items_from_diffs(diff_elements)
        store.write_local_data([x.to_dict() for x in to_save])
        logger.info("Finished freeze")


@app.command()
def configure(
    force: Annotated[
        Optional[bool],
        typer.Option(
            "--force",
            help="Replace existing configuration.",
            show_default=False,
        ),
    ] = False,
    rules: Annotated[
        Optional[bool],
        typer.Option(
            "--rules",
            help=(
                "Configure service's branch rules"
                " (Note: this will prevent pushes to the default branch!)"
            ),
            show_default=False,
        ),
    ] = False,
    workflow: Annotated[
        Optional[bool],
        typer.Option(
            "--workflow",
            help="Creates workflows, issue templates and PR templates.",
            show_default=False,
        ),
    ] = False,
    release_templates: Annotated[
        list[LocalStore.ReleaseTemplateSet],
        typer.Option(
            help=(
                "Release file template sets to install in qw_release_templates"
                " (and so be used by qw release)"
            ),
            show_default=False,
        ),
        # Stop mypy, ruff and black from fighting each other.
    ] = [],  # noqa: B006
):
    """Configure remote repository for qw (after initialisation and login credentials added)."""
    if not (rules or workflow or release_templates):
        typer.echo(
            "Nothing to do. Please provide at least one option from"
            " --service-templates, --release-templates, or --ci",
        )
        return 0
    service = _build_and_check_service()
    repo_updated = False
    if workflow:
        store.write_templates_and_ci(service, force=force)
        repo_updated = True
    for template_set in release_templates:
        store.write_release_document_templates(
            service,
            template_set,
            force=force,
        )
        repo_updated = True
    if repo_updated:
        typer.echo(
            "Local repository updated, please commit the changes made to your local repository.",
        )
    if rules:
        service.update_remote(force=force)
        typer.echo(
            "Updated remote repository with rules",
        )
        return None
    return None


@app.command()
def generate_merge_fields(
    output: Annotated[
        Path,
        typer.Option(
            help="Output file name",
            writable=True,
        ),
    ] = Path("fields.csv"),
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
    for cls in DESIGN_STAGE_CLASSES:
        name = cls.design_stage.value
        fields = cls.base_fields | cls.not_required_fields
        for f in fields:
            field = f"{name}.{f}"
            headings.append(field)
            examples.append(f"<{field}>")
    with output.open("w") as out:
        out.write("\n".join([",".join(line) for line in [headings, examples]]))


@app.command()
def release():
    """Produce documentation by merging frozen values into templates."""
    data = _get_merge_data()
    for wt_path, wt_out in store.release_word_templates():
        doc = load_template(wt_path)
        doc.write(
            output_file=wt_out,
            data=data,
            filter_referencers=filter_data_references,
        )


def filter_data_references(from_obj_type, from_objs, to_obj_type, to_obj):
    """
    Find backreferences.

    Finds the objects in the from_objs iterable that refer to to_obj.
    """
    to_obj_class = get_design_stage_class_from_name(to_obj_type)
    if to_obj_class is None:
        return None
    is_backref = to_obj_class.is_dict_reference(to_obj, from_obj_type)
    if is_backref is None:
        return None
    logger.debug("Can we find any in {}", from_objs)
    return filter(is_backref, from_objs)


def _get_merge_data() -> dict[str, list[dict[str, Any]]]:
    """Fetch frozen data for MS Word merge."""
    stages = get_local_stages(store)
    data: dict[str, list[dict[str, Any]]] = {}
    for s in stages:
        sd = s.to_dict()
        typ = sd["stage"].value
        if typ not in data:
            data[typ] = []
        data[typ].append(sd)
    return data


def run_app():
    """Run the app, reporting errors nicely."""
    try:
        app()
        sys.exit(0)
    except QwError as e:
        sys.stderr.write(str(e) + "\n")
        sys.exit(2)


if __name__ == "__main__":
    run_app()
