"""Interaction with the qw local configuration and data storage."""
import json

from loguru import logger

from qw.base import QwError
from qw.local_store.directories import _find_conf_dir


def get_configuration() -> dict:
    """Get the configuration (as a dict) from the .qw/conf.json file."""
    conf_file_name = _find_conf_dir() / "conf.json"
    if not conf_file_name.is_file():
        msg = (
            "Could not find a configuration directory, please"
            " initialize with `qw init`"
        )
        raise QwError(
            msg,
        )
    with conf_file_name.open() as conf:
        return json.load(conf)


def write_to_config(qw_dir, repo, reponame, service, username):
    """Write configuration to qw config file."""
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
