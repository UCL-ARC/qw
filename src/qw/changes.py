"""Compares changes between remote and local data, allowing the user to make decisions."""
from collections import defaultdict

from loguru import logger
from rich.prompt import Confirm, Prompt

from qw.design_stages.main import DesignStages, get_local_stages, get_remote_stages
from qw.local_store.main import LocalStore
from qw.remote_repo.service import GitService


class ChangeHandler:
    """Allow user interaction to manage changes between local and remote design stage data."""

    def __init__(self, service: GitService, store: LocalStore):
        """Create ChangeHandler instance."""
        self._service = service
        self._store = store

    def combine_local_and_remote_items(self) -> list[DesignStages]:
        """Compare local and remote design stages and prompt on any differences."""
        paired = self._pair_remote_and_local()

        output_items = []
        for internal_id, pair in paired.items():
            remote_item: DesignStages | None = pair.get("remote")
            local_item: DesignStages | None = pair.get("local")
            if not local_item:
                # TODO add nice representation of DesignStage so we can have a summary by printing that
                logger.info(f"New remote item: {remote_item}")
                output_items.append(remote_item)
                continue

            if not remote_item:
                output_items.extend(self._prompt_to_remove_local_item(local_item))
                continue

            diff = local_item.diff(remote_item)
            if not diff:
                output_items.append(local_item)
                continue

            output_items.append(
                self._prompt_for_version_change(
                    diff,
                    internal_id,
                    local_item,
                    remote_item,
                ),
            )

        return output_items

    def _pair_remote_and_local(self) -> dict[int, dict[str, DesignStages]]:
        paired_data: dict[int, dict[str, DesignStages]] = defaultdict(dict)

        for stage in get_remote_stages(self._service):
            paired_data[stage.internal_id]["remote"] = stage

        for stage in get_local_stages(self._store):
            paired_data[stage.internal_id]["local"] = stage

        return paired_data

    @staticmethod
    def _prompt_to_remove_local_item(local_item) -> list[DesignStages]:
        if Confirm.ask(
            f"{local_item} no longer exists in remote, would you like to remove it from the local store?",
        ):
            return []
        return [local_item]

    def _prompt_for_version_change(
        self,
        diff: dict[str, dict],
        internal_id: int,
        local_item: DesignStages,
        remote_item: DesignStages,
    ):
        lines = []
        for field, differences in diff.items():
            lines.append(
                f"Changes found between local and remote data for item {internal_id}:",
            )
            lines.append(f"{field} Local:")
            lines.append(differences["self"])
            lines.append("")
            lines.append(
                f"{field} {self._service.username}/{self._service.reponame}:",
            )
            lines.append(differences["other"])
            lines.append("\n")
        logger.info("\n".join(lines))
        response = Prompt.ask(
            "Would you like to do",
            choices=[
                "Nothing",
                "Update without version increment",
                "Update and increment version",
            ],
        )
        if response == "Nothing":
            return local_item
        if response == "Update without version increment":
            return remote_item
        # TODO add in version to increment it
        return remote_item
