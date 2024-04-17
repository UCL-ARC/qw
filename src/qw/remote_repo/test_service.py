"""Mock service functionality to allow reading from local filesystem in tests rather than hitting APIs constantly."""
import re
from collections.abc import Iterable
from itertools import chain
from pathlib import Path

import frontmatter

from qw.base import QwError
from qw.design_stages.categories import RemoteItemType
from qw.md import text_under_heading
from qw.remote_repo.service import GitService, Issue, PullRequest


class FileSystemIssue(Issue):
    """An issue on local filesystem."""

    def __init__(self, markdown_data) -> None:
        """Initialize the issue."""
        self.markdown_data = markdown_data

    @property
    def number(self) -> int:
        """Get the number (human-readable ID)."""
        return self.markdown_data["number"]

    @property
    def title(self) -> str:
        """Get the title."""
        return self.markdown_data["title"]

    @property
    def labels(self) -> list[str]:
        """Get the label names for the issue."""
        return self.markdown_data["labels"]

    @property
    def body(self) -> str:
        r"""Get the body of the first comment."""
        return self.markdown_data.content

    @property
    def item_type(self) -> RemoteItemType:
        """Get the type of the issue, as we may handle a pull request differently to an issue."""
        item_type = self.markdown_data["type"]
        if item_type == "request":
            return RemoteItemType.REQUEST
        if item_type == "issue":
            return RemoteItemType.ISSUE
        msg = f"Unknown type in markdown: '{item_type}'"
        raise QwError(msg)


class FileSystemPullRequest(PullRequest, FileSystemIssue):
    """Pull Request from the FileSystem test git service."""

    @property
    def item_type(self) -> RemoteItemType:
        """Report that this is a request."""
        return RemoteItemType.REQUEST

    @property
    def closing_issues(self) -> list[int]:
        """Closing issues are derived from finding "closes #<num>" in the content."""
        return [int(g) for g in re.findall(r"(?:Closes|closes)\s+#(\d+)", self.body)]

    @property
    def paths(self) -> list[str]:
        """Returns all nonblank lines after "### Paths" in the body."""
        text = text_under_heading(self.body, "Paths")
        return [line for line in re.split(r"\n+", text) if line]


def build_file_system_issue(filepath):
    """Create the appropriate FileSystemIssue."""
    markdown_data = frontmatter.load(filepath)
    item_type = markdown_data["type"]
    if item_type == "request":
        return FileSystemPullRequest(markdown_data)
    if item_type == "issue":
        return FileSystemIssue(markdown_data)
    msg = f"Unknown type in markdown: '{item_type}'"
    raise QwError(msg)


class FileSystemService(GitService):
    """The FileSystem Service."""

    def __init__(self, root_dir: Path, target_dir: str):
        """Set up mocked service reading from local filesystem."""
        super().__init__({"user_name": "file", "repo_name": "system"})
        self.resource_path = root_dir / target_dir
        mdx_files = sorted(self.resource_path.glob("*.mdx"))
        self.issue_objects = [build_file_system_issue(file) for file in mdx_files]

    def get_issue(self, number: int):
        """Get the issue with the specified number."""
        matching_issues = [i for i in self.issues if i.number == number]

        if len(matching_issues) == 0:
            msg = "No issues found with number {number}"
            raise QwError(msg)
        if len(matching_issues) != 1:
            msg = "No multiple issues found with {number}"
            raise QwError(msg)

        return matching_issues[0]

    @property
    def issues(self):
        """Get all issues in the root path."""
        return filter(
            lambda x: not isinstance(x, FileSystemPullRequest),
            self.issue_objects,
        )

    @property
    def pull_requests(self):
        """Get all pull requests in the root path."""
        return filter(
            lambda x: isinstance(x, FileSystemPullRequest),
            self.issue_objects,
        )

    def check(self):
        """Check that the credentials can connect to the service."""
        return True

    @property
    def template_paths(self) -> Iterable[Path]:
        """Paths for templates to copy to the service."""
        markdown = self.qw_resources.glob("templates/.github/**/*.md*")
        yaml = self.qw_resources.glob("templates/.github/**/*.yml*")
        return chain(markdown, yaml)

    def update_remote(self, *, force: bool) -> None:
        """No implementation as no remote."""
        ...
