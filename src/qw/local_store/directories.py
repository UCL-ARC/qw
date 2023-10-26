"""Local qw store directories."""
import pathlib

from loguru import logger

from qw.base import QwError


def find_git_base_dir() -> pathlib.Path:
    """Find the base directory for the local git repository."""
    git_dir = _find_aunt_dir(
        ".git",
        "We are not in a git project, so we cannot initialize!",
    )
    return git_dir.parent


def _find_aunt_dir(name: str, error_msg: str) -> pathlib.Path:
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


def _find_conf_dir() -> pathlib.Path:
    """Return the .qw directory of the project we are in."""
    return _find_aunt_dir(
        ".qw",
        "Could not find a configuration directory, please initialize with `qw init`",
    )


def get_or_create_qw_dir(base: pathlib.Path, *, force: bool = False) -> pathlib.Path:
    """
    Create QW directory.

    :param base: Base directory
    :param force: force re-initialisation.
    :return Path: qw directory
    """
    qw_dir = base / ".qw"
    logger.debug(".qw directory is '{dir}'", dir=qw_dir)
    if qw_dir.is_file():
        msg = ".qw file exists, which is blocking us from making a .qw directory. Please delete it!"
        raise QwError(msg)
    if not qw_dir.is_dir():
        qw_dir.mkdir()
    elif not force:
        msg = ".qw directory already exists! Use existing configuration or use --force flag to reinitialize!"
        raise QwError(msg)
    return qw_dir
