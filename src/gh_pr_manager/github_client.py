from __future__ import annotations

"""Utilities for interacting with GitHub via the ``gh`` CLI."""

from .utils import run_cmd


def check_auth_status() -> bool:
    """Return ``True`` if the user is authenticated with the ``gh`` CLI."""
    success, _ = run_cmd(["gh", "auth", "status"])
    return success


def get_user_login() -> str | None:
    """Return the login of the authenticated GitHub user, or ``None`` on error."""
    success, output = run_cmd(["gh", "api", "user", "--jq", ".login"])
    if success:
        return output.strip()
    return None


def get_user_orgs() -> list[str]:
    """Return a list of organization logins for the current user."""
    success, output = run_cmd(["gh", "api", "user/orgs", "--jq", "'.[].login'"])
    if not success:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def get_repos(owner: str) -> list[str]:
    """Return a list of repository full names for the given owner."""
    repos: list[str] = []
    page = 1
    while True:
        path = f"users/{owner}/repos?per_page=100&page={page}"
        success, output = run_cmd(["gh", "api", path, "--jq", "'.[].full_name'"])
        if not success:
            break
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        repos.extend(lines)
        if len(lines) < 100:
            break
        page += 1
    return repos

