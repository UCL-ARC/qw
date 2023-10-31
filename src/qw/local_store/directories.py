"""Local qw store directories."""
import pathlib

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
