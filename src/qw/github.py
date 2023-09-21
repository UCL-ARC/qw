"""
Github concrete service
"""

import github3
import keyring

import qw.service


class Issue(qw.service.Issue):
    def __init__(self, issue) -> None:
        self.issue = issue

    def number(self) -> int:
        return self.issue.number

    def title(self) -> str:
        return self.issue.title


class Service(qw.service.Service):
    def __init__(self, conf):
        """Gets the gh auth token and logs into github with it."""
        super().__init__(conf)
        token = keyring.get_password("gh:github.com", "")
        self.gh = github3.login(token=token)

    def get_issue(self, number: int):
        issue = self.gh.issue(self.username, self.reponame, number)
        return Issue(issue)
