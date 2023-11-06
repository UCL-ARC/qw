"""Factory for making git hosting services."""

from qw.base import QwError
from qw.local_store.main import LocalStore
from qw.remote_repo._github import GitHubService
from qw.remote_repo.service import GitService, Service
from qw.remote_repo.test_service import FileSystemService


def get_service(conf: dict | None = None) -> GitService:
    """Return a git hosting service."""
    if conf is None:
        store = LocalStore()
        conf = store.get_configuration()
    name = conf.get("service", None)
    if name is None:
        msg = "Configuration is corrupt. Please run `qw init`"
        raise QwError(
            msg,
        )
    if name == str(Service.GITHUB):
        return GitHubService(conf)
    if name == str(Service.TEST):
        return FileSystemService("test")

    msg = f"Do not know how to connect to the {name} service!"
    raise QwError(
        msg,
    )
