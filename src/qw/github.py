"""Github concrete service."""

import github3
import keyring

import qw.service


class Issue(qw.service.Issue):
    """An issue on github."""

    def __init__(self, issue) -> None:
        """
        Initialize the issue.

        Use service.get_issue(number) instead.
        """
        self.issue = issue

    def number(self) -> int:
        """Get the number (human readable ID)."""
        return self.issue.number

    def title(self) -> str:
        """Get the title."""
        return self.issue.title


class Service(qw.service.GitService):
    """The github service."""

    def __init__(self, conf):
        """Log in with the gh auth token."""
        super().__init__(conf)
        token = keyring.get_password("gh:github.com", "")
        self.gh = github3.login(token=token)

    def get_issue(self, number: int):
        """Get the issue with the specified number."""
        issue = self.gh.issue(self.username, self.reponame, number)
        return Issue(issue)
