import pytest
from gh_pr_manager import github_client

@pytest.fixture(autouse=True)
def _mock_auth(monkeypatch):
    monkeypatch.setattr(github_client, "check_auth_status", lambda: True)
    monkeypatch.setattr(github_client, "get_user_login", lambda: "me")
    monkeypatch.setattr(github_client, "get_user_orgs", lambda: ["org"])
    monkeypatch.setattr(github_client, "get_repos", lambda owner: [f"{owner}/repo"])
    yield

