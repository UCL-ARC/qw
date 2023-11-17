"""GitHub concrete service."""
import json
from collections.abc import Iterable
from itertools import chain
from pathlib import Path

import github3
import keyring
import requests
from github3.exceptions import AuthenticationFailed
from jinja2 import Template
from loguru import logger
from requests import Response

import qw.remote_repo.service
from qw.base import QwError
from qw.design_stages.categories import RemoteItemType


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
        token = self._get_token()
        if not token:
            msg = "Could not find a token in keyring."
            raise QwError(msg)
        self.gh = github3.login(token=token)

    def _get_token(self):
        return keyring.get_password("qw", f"{self.username}/{self.reponame}")

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

    def check(self) -> bool:
        """Check that the credentials can connect to the service."""
        try:
            logger.info(
                "There are currently {issues} issues and PRs",
                issues=len(self.issues),
            )
        except ConnectionError as exception:
            msg = "Could not connect to Github, please check internet connection"
            raise QwError(msg) from exception
        except AuthenticationFailed as exception:
            msg = "Could not connect to Github, please check that your access token is correct and has not expired"
            raise QwError(msg) from exception
        return True

    @property
    def template_paths(self) -> Iterable[Path]:
        """Paths for templates to copy to the service."""
        markdown = self.qw_resources.glob("templates/.github/**/*.md*")
        yaml = self.qw_resources.glob("templates/.github/**/*.yml*")
        return chain(markdown, yaml)

    def update_remote(self, *, force: bool) -> None:
        """Update remote repository with configration for qw tool."""
        # load configured ruleset as a python dict
        ruleset_template = self.qw_resources / "remote_repo/github/ruleset.json.jinja2"
        json_template = Template(ruleset_template.read_text())
        json_text = json_template.render(org=self.username, user=self.reponame)
        json_bundle = json.loads(json_text)

        # POST ruleset to GitHub
        ruleset_url = (
            f"https://api.github.com/repos/{self.username}/{self.reponame}/rulesets"
        )
        token = self._get_token()
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if not force:
            self._create_new_ruleset(headers, json_bundle, ruleset_url)
            return

        existing_ruleset_response = requests.get(
            ruleset_url,
            headers=headers,
            timeout=10,
        )
        if not self._is_valid_response(existing_ruleset_response):
            self._throw_from_response(existing_ruleset_response)
        existing_rulesets = existing_ruleset_response.json()
        ruleset_id = None
        for ruleset in existing_rulesets:
            if json_bundle["name"] == ruleset["name"]:
                ruleset_id = ruleset["id"]
                break
        if not ruleset_id:
            self._create_new_ruleset(headers, json_bundle, ruleset_url)
        else:
            self._update_ruleset(headers, json_bundle, ruleset_url, ruleset_id)

    def _is_valid_response(self, response: Response):
        http_created = 201
        http_updated = 200
        return response.status_code in (http_created, http_updated)

    def _throw_from_response(self, response: Response):
        response_bundle = response.json()
        msg = f"Error with GitHub rulesets - {response_bundle['message']}: {'. '.join(response_bundle['errors'])}"
        raise QwError(
            msg,
        )

    def _create_new_ruleset(self, headers: dict, json_bundle: dict, ruleset_url: str):
        response = requests.post(
            ruleset_url,
            json=json_bundle,
            headers=headers,
            timeout=10,
        )
        # check response and raise if it hasn't been created
        if self._is_valid_response(response):
            logger.info(
                "Added '{ruleset_name}' to {org}/{repo}",
                ruleset_name=json_bundle["name"],
                org=self.username,
                repo=self.reponame,
            )
            return
        self._throw_from_response(response)

    def _update_ruleset(
        self,
        headers: dict,
        json_bundle: dict,
        ruleset_url: str,
        ruleset_id: int,
    ):
        update_url = f"{ruleset_url}/{ruleset_id}"
        response = requests.put(
            update_url,
            json=json_bundle,
            headers=headers,
            timeout=10,
        )
        # check response and raise if it hasn't been updated
        if self._is_valid_response(response):
            logger.info(
                "Updated '{ruleset_name}' to {org}/{repo}",
                ruleset_name=json_bundle["name"],
                org=self.username,
                repo=self.reponame,
            )
            return
        self._throw_from_response(response)
