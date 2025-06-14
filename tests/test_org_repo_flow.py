import json
import pytest

from gh_pr_manager import main
from gh_pr_manager.main import PRManagerApp, OrgSelector, RepoSelectionWidget
from gh_pr_manager import github_client


@pytest.mark.asyncio
async def test_org_and_repo_selection_saves_config(tmp_path, monkeypatch):
    conf = tmp_path / "config.json"
    monkeypatch.setattr(main, "CONFIG_PATH", conf)
    monkeypatch.setattr(github_client, "get_user_login", lambda: "me")
    monkeypatch.setattr(github_client, "get_user_orgs", lambda: ["org"])
    monkeypatch.setattr(github_client, "get_repos", lambda owner: [f"{owner}/r1", f"{owner}/r2"])    

    app = PRManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert pilot.app.query_one(OrgSelector)
        pilot.app.on_owner_selected("org")
        await pilot.pause()
        assert pilot.app.query_one(RepoSelectionWidget)
        pilot.app.on_repo_selected("org/r1")
        await pilot.pause()

    data = json.loads(conf.read_text())
    assert data["selected_repository"] == "org/r1"
