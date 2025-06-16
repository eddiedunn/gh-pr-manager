from __future__ import annotations

"""Utilities for interacting with GitHub via the ``gh`` CLI."""

from typing import Optional
from .utils import run_cmd


def check_auth_status() -> bool:
    """Return ``True`` if the user is authenticated with the ``gh`` CLI."""
    success, _ = run_cmd(["gh", "auth", "status"])
    return success


def get_user_login() -> Optional[str]:
    """Return the login of the authenticated GitHub user, or ``None`` on error."""
    success, output = run_cmd(["gh", "api", "user", "--jq", ".login"])
    if success:
        return output.strip()
    return None


def get_user_orgs() -> list[str]:
    """Return a list of organization logins for the current user."""
    success, output = run_cmd(["gh", "api", "user/orgs", "--jq", ".[].login"])
    if not success:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def get_repos(owner: str) -> list[str]:
    """Return a list of repository full names for the given owner."""
    repos: list[str] = []
    page = 1
    import logging
    logging.basicConfig(filename="org_selector_debug.log", level=logging.INFO, filemode="a")
    from . import github_client
    user_login = github_client.get_user_login()
    while True:
        if owner == user_login:
            path = f"user/repos?per_page=100&page={page}"
        else:
            path = f"users/{owner}/repos?per_page=100&page={page}"
        logging.info(f"DEBUG get_repos: fetching {path}")
        success, output = run_cmd(["gh", "api", path, "--jq", ".[].full_name"]);
        if not success:
            logging.info(f"DEBUG get_repos: failed to fetch {path}, output={output!r}")
            break
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        repos.extend(lines)
        if len(lines) < 100:
            break
        page += 1
    logging.info(f"DEBUG get_repos: found {len(repos)} repos for owner={owner}")
    return repos

