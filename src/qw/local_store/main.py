"""Interaction with the qw local configuration and data storage."""
import os
import pathlib
import shutil
from pathlib import Path

from loguru import logger

from qw.base import QwError
from qw.local_store._json import _dump_json, _load_json
from qw.local_store._repository import RequirementComponents
from qw.local_store.directories import find_git_base_dir
from qw.remote_repo.service import GitService, Service


class LocalStore:
    """Local storage of configuration, design stages and interaction with the local repository configuration."""

    _config_file = "conf.json"
    _data_file = "store.json"

    def __init__(self, base_dir: Path | None = None):
        """Find base dir if not defined."""
        self.base_dir = base_dir if base_dir else find_git_base_dir()

        self.qw_dir = self.base_dir / ".qw"
        self._requirement_component = RequirementComponents(self.qw_dir)

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
            msg = "Could not find a configuration directory, please initialize with `qw init`"
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

    def initialise_qw_files(
        self,
        repo: str,
        reponame: str,
        service: Service,
        username: str,
    ):
        """Write all configuration files in the qw directory."""
        self._write_config_file(repo, reponame, service, username)
        self._requirement_component.write_initial_data_if_not_exists()

    def _write_config_file(self, repo, reponame, service, username):
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

    def write_templates_and_ci(self, service: GitService, *, force: bool):
        """Write templates and CI configuration to local repository."""
        logger.info(
            "Writing templates and CI config to local repository, force={force}",
            force=force,
        )
        should_not_exist = []
        target_paths = []
        for template in service.template_paths:
            target_path = self.base_dir / service.relative_target_path(
                "templates",
                template,
            )
            # remove .jinja2 suffix from target
            if target_path.suffix == ".jinja2":
                target_path = target_path.with_suffix("")
            target_paths.append(target_path)
            if not force and target_path.exists():
                should_not_exist.append(target_path)

        if should_not_exist:
            msg = f"Templates already exists, rerun with '--force' to override existing templates:'n {should_not_exist}"
            raise QwError(msg)

        for source_path, target_path in zip(
            service.template_paths,
            target_paths,
            strict=True,
        ):
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if target_path.stem == "requirement":
                self._requirement_component.update_requirements_template(
                    source_path,
                    target_path,
                )
            else:
                shutil.copy(source_path, target_path)

    def release_word_templates(self, out_dir=None):
        """
        Iterates through qw_release_templates/*.docx files.

        Returns a pair (in_path, out_path) where in_path is the path
        of the template file and out_path is the path it should be
        written to.
        """
        if out_dir is None:
            out_dir = self.base_dir / "qw_release_out"
        top = self.base_dir / "qw_release_templates"
        for (dirpath, _dirnames, filenames) in os.walk(top):
            out_path = out_dir / os.path.relpath(dirpath, top)
            for filename in filenames:
                if os.path.splitext(filename)[1] == ".docx":
                    yield (
                        os.path.join(dirpath, filename),
                        os.path.join(out_path, filename),
                    )
