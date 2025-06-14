import pytest
from gh_pr_manager import github_client

@pytest.fixture(autouse=True)
def _mock_auth(monkeypatch):
    monkeypatch.setattr(github_client, "check_auth_status", lambda: True)
    yield

