"""Local qw store directories."""
import pathlib


def find_git_base_dir() -> pathlib.Path | None:
    """Find the base directory for the local git repository."""
    git_dir = _find_aunt_dir(".git")
    if git_dir is None:
        return None
    return git_dir.parent


def _find_aunt_dir(name: str) -> pathlib.Path | None:
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
            return None
        d = d.parent
