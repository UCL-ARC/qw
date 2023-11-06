"""GitHub concrete service."""

import github3
from github3.exceptions import AuthenticationFailed
from loguru import logger

import qw.remote_repo.service
from qw.base import QwError
from qw.design_stages.categories import RemoteItemType
from qw.local_store.keyring import get_qw_password


class Issue(qw.remote_repo.service.Issue):
    """An issue on GitHub."""

    def __init__(self, issue) -> None:
        """
        Initialize the issue.

        Use service.get_issue(number) instead.
        """
        self._issue = issue

    @property
    def number(self) -> int:
        """Get the number (human-readable ID)."""
        return self._issue.number

    @property
    def title(self) -> str:
        """Get the title."""
        return self._issue.title.strip()

    @property
    def labels(self) -> list[str]:
        """Get the label names for the issue."""
        return [label.name for label in self._issue.labels()]

    @property
    def body(self) -> str:
        r"""Get the body of the first comment, always using `\n` as the newline character."""
        return "\n".join(self._issue.body.splitlines())

    @property
    def item_type(self) -> RemoteItemType:
        """Get the type of the issue, as we may handle a pull request differently to an issue."""
        if self._issue.as_dict().get("pull_request"):
            return RemoteItemType.REQUEST
        return RemoteItemType.ISSUE


class GitHubService(qw.remote_repo.service.GitService):
    """The GitHub service."""

    def __init__(self, conf):
        """Log in with the gh auth token."""
        super().__init__(conf)
        token = get_qw_password(self.username, self.reponame)
        if not token:
            msg = "Could not find a token in keyring."
            raise QwError(msg)
        self.gh = github3.login(token=token)

    def get_issue(self, number: int):
        """Get the issue with the specified number."""
        issue = self.gh.issue(self.username, self.reponame, number)
        return Issue(issue)

    @property
    def issues(self):
        """Get all issues for the repository."""
        return [
            Issue(issue) for issue in self.gh.issues_on(self.username, self.reponame)
        ]

    def check(self):
        """Check that the credentials can connect to the service."""
        try:
            logger.info(self.issues)
        except ConnectionError as exception:
            msg = "Could not connect to Github, please check internet connection"
            raise QwError(msg) from exception
        except AuthenticationFailed as exception:
            msg = "Could not connect to Github, please check that your access token is correct and has not expired"
            raise QwError(msg) from exception
