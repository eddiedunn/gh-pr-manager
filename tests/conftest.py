import pytest
from gh_pr_manager import github_client


@pytest.fixture(autouse=True)
def mock_github(monkeypatch):
    """Provide fake GitHub data so tests never hit the network."""
    monkeypatch.setattr(github_client, "check_auth_status", lambda: True)
    monkeypatch.setattr(github_client, "get_user_login", lambda: "me")
    monkeypatch.setattr(github_client, "get_user_orgs", lambda: ["org"])
    monkeypatch.setattr(
        github_client,
        "get_repos",
        lambda owner: [f"{owner}/repo1", f"{owner}/repo2"],
    )
    yield
