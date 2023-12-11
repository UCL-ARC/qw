"""Compares changes between remote and local data, allowing the user to make decisions."""
from collections import OrderedDict, defaultdict

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from qw.design_stages.main import DesignStages, get_local_stages, get_remote_stages
from qw.local_store.main import LocalStore
from qw.remote_repo.service import GitService


class ChangeHandler:
    """Allow user interaction to manage changes between local and remote design stage data."""

    class DiffElement:
        """A potential update to the local store."""

        def __init__(
            self,
            service: GitService,
            local_item: DesignStages | None,
            remote_item: DesignStages | None,
        ):
            """
            Initialize.

            :param service: The Git service object.
            :param local_item: The "self" (local) item of the diff.
            :param remote_item: The "other" (remote) item of the diff.
            """
            self._service = service
            self._diff = None
            if local_item is not None and remote_item is not None:
                self._diff = local_item.diff(remote_item)
            self._local_item = local_item
            self._remote_item = remote_item

        def show(self):
            """Show this difference on the screen."""
            if not bool(self._diff):
                return
            table = Table(
                title=f"Changes detected for {self._local_item}:",
                show_lines=True,
                expand=True,
            )
            table.add_column("Field", justify="right", style="cyan")
            table.add_column("Local", justify="left", style="magenta")
            table.add_column(
                f"{self._service.username}/{self._service.reponame}",
                justify="left",
                style="green",
            )
            for field, differences in self._diff.items():
                table.add_row(field, differences["self"], differences["other"])

            Console().print(table)

        def prompt_for_version_change(self):
            """
            Prompt the user for what they want to do with this diff.

            :return: The item so be stored in the local store; either
            the local item (for no change) or the remote item (possibly
            with the version number incremented).
            """
            if not bool(self._diff):
                if self._local_item is None:
                    # New remote item, no prompt required
                    return self._remote_item
                if self._remote_item is not None:
                    # Both exist, but no difference
                    return self._local_item
                # Only local exists, remote has been deleted
                if Confirm.ask(
                    f"{self._local_item} no longer exists in remote, would you like to remove it from the local store?",
                ):
                    # Remove the local item
                    return None
                # Keep the local item
                return self._local_item
            prompt = "\n".join(
                [
                    "Would you like to:",
                    "n (Don't save the update)",
                    "u (Update, but trivial change so don't increment the version)",
                    "i (Update and increment the version)",
                    "",
                ],
            )

            response = Prompt.ask(prompt, choices=["n", "u", "i"])
            if response == "n":
                return self._local_item
            if response == "i":
                self._remote_item.version += 1
            return self._remote_item

    def __init__(self, service: GitService, store: LocalStore):
        """Create ChangeHandler instance."""
        self._service = service
        self._store = store

    def combine_local_and_remote_items(self) -> list[DesignStages]:
        """Compare local and remote design stages and prompt on any differences."""
        diff_elements = self.diff_remote_and_local_items()
        return self.get_local_items_from_diffs(diff_elements)

    def diff_remote_and_local_items(self) -> list[DiffElement]:
        """
        Find all differences between local and remote design stages.

        :return: A list of diff elements, each of which is an item
        that differs between the local store and the remote service.
        """
        paired = self._pair_remote_and_local()

        diff_elements = []
        for _internal_id, pair in paired.items():
            diff_elements.append(
                ChangeHandler.DiffElement(
                    self._service,
                    pair.get("local"),
                    pair.get("remote"),
                ),
            )

        return diff_elements

    @classmethod
    def get_local_items_from_diffs(
        cls,
        diff_elements: list[DiffElement],
    ) -> list[DesignStages]:
        """
        Transform DiffElements into local items to be stored.

        :param diff_elements: An iterable of DiffElements, each
        representing a difference between the remote and local
        items.
        :return: A list of local items to be set in the store.
        """
        output_items = []
        for diff_element in diff_elements:
            diff_element.show()
            output_item = diff_element.prompt_for_version_change()
            if output_item is not None:
                output_items.append(output_item)

        return output_items

    def _pair_remote_and_local(self) -> dict[int, dict[str, DesignStages]]:
        paired_data: dict[int, dict[str, DesignStages]] = defaultdict(dict)

        for stage in get_remote_stages(self._service):
            paired_data[stage.internal_id]["remote"] = stage

        for stage in get_local_stages(self._store):
            paired_data[stage.internal_id]["local"] = stage

        return OrderedDict(sorted(paired_data.items()))
