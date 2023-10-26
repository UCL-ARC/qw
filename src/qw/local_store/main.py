"""Interaction with the qw local configuration and data storage."""
from loguru import logger

from qw.base import QwError
from qw.local_store._json import _dump_json, _load_json
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
    return _load_json(conf_file_name)


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
    _dump_json(conf, conf_file_name)
