"""Interaction with the qw local configuration and data storage."""
import pathlib
from pathlib import Path

from loguru import logger

from qw.base import QwError
from qw.local_store._json import _dump_json, _load_json
from qw.local_store.directories import find_git_base_dir
from qw.remote_repo.service import Service


class LocalStore:
    """Local storage of configuration and design stages."""

    _config_file = "conf.json"
    _data_file = "store.json"

    def __init__(self, base_dir: Path | None = None):
        """Find base dir if not defined."""
        self.base_dir = base_dir if base_dir else find_git_base_dir()

        self.qw_dir = self.base_dir / ".qw"

    @property
    def _config_path(self):
        return self.qw_dir / self._config_file

    @property
    def _data_path(self):
        return self.qw_dir / self._data_file

    def get_or_create_qw_dir(self, *, force: bool = False) -> pathlib.Path:
        """
        Create QW directory.

        :param force: force re-initialisation.
        :return Path: qw directory
        """
        logger.debug(".qw directory is '{dir}'", dir=self.qw_dir)
        if self.qw_dir.is_file():
            msg = ".qw file exists, which is blocking us from making a .qw directory. Please delete it!"
            raise QwError(msg)
        if not self.qw_dir.is_dir():
            self.qw_dir.mkdir()
        elif not force:
            msg = ".qw directory already exists! Use existing configuration or use --force flag to reinitialize!"
            raise QwError(msg)
        return self.qw_dir

    def read_configuration(self) -> dict:
        """Get the configuration (as a dict) from the .qw/conf.json file."""
        if not self._config_path.is_file():
            msg = (
                "Could not find a configuration directory, please"
                " initialize with `qw init`"
            )
            raise QwError(
                msg,
            )
        return _load_json(self._config_path)

    def read_local_data(self) -> list[dict]:
        """Read persisted data stages."""
        if not self._data_path.exists():
            logger.debug("No existing data file, returning empty list")
            return []
        return _load_json(self._data_path)

    def write_to_config(
        self,
        repo: str,
        reponame: str,
        service: Service,
        username: str,
    ):
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
        _dump_json(conf, self._config_path)

    def write_local_data(self, data: list[dict]):
        """Write to local data file."""
        _dump_json(data, self._data_path)
