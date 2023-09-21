"""Factory for making git hosting services."""

import qw.github
import qw.service
from qw.base import QwError


def get_service(conf: dict | None = None) -> qw.service.GitService:
    """Return a git hosting service."""
    if conf is None:
        conf = qw.service.get_configuration()
    name = conf.get("service", None)
    if name is None:
        msg = "Configuration is corrupt. Please run `qw init`"
        raise QwError(
            msg,
        )
    if name == str(qw.service.Service.GITHUB):
        return qw.github.Service(conf)
    msg = f"Do not know how to connect to the {name} service!"
    raise QwError(
        msg,
    )
