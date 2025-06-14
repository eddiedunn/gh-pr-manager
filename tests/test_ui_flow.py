import json
from pathlib import Path

import pytest

from gh_pr_manager import main, utils
from gh_pr_manager.main import PRManagerApp, BranchSelector


@pytest.mark.asyncio
async def test_full_ui_flow(tmp_path, monkeypatch):
    """Select org and repo then show branches."""
    conf = tmp_path / "config.json"
    conf.write_text(json.dumps({"selected_repository": ""}))
    monkeypatch.setattr(main, "CONFIG_PATH", conf)

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)

    repo_path = home / ".cache" / "gh_pr_manager" / "org/repo1"
    calls: list[tuple[list[str], str | None]] = []

    def fake_run(cmd, cwd=None):
        calls.append((cmd, cwd))
        if cmd[:4] == ["git", "-C", str(repo_path), "for-each-ref"]:
            return True, "origin/main\norigin/feature\n"
        return True, ""

    monkeypatch.setattr(utils, "run_cmd", fake_run)
    monkeypatch.setattr(main, "run_cmd", fake_run)

    app = PRManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        pilot.app.on_owner_selected("org")
        await pilot.pause()
        pilot.app.on_repo_selected("org/repo1")
        await pilot.pause()
        assert pilot.app.query_one(BranchSelector)

    # first call should clone since repo doesn't exist
    assert ["gh", "repo", "clone", "org/repo1", str(repo_path)] in [c[0] for c in calls]
