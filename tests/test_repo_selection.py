import json
from pathlib import Path

import pytest

from gh_pr_manager import main, utils
from gh_pr_manager.main import PRManagerApp


@pytest.mark.asyncio
async def test_clone_when_missing(tmp_path, monkeypatch):
    conf = tmp_path / "config.json"
    conf.write_text(json.dumps({"selected_repository": ""}))
    monkeypatch.setattr(main, "CONFIG_PATH", conf)
    monkeypatch.setattr(PRManagerApp, "CONFIG_PATH", conf, raising=False)

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)

    repo_path = home / ".cache" / "gh_pr_manager" / "org/repo1"
    calls: list[list[str]] = []

    def fake_run(cmd, cwd=None):
        calls.append(cmd)
        if cmd[:4] == ["git", "-C", str(repo_path), "for-each-ref"]:
            return True, ""
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

    assert ["gh", "repo", "clone", "org/repo1", str(repo_path)] in calls
    assert ["git", "-C", str(repo_path), "pull"] not in calls


@pytest.mark.asyncio
async def test_pull_when_cloned(tmp_path, monkeypatch):
    conf = tmp_path / "config.json"
    conf.write_text(json.dumps({"selected_repository": ""}))
    monkeypatch.setattr(main, "CONFIG_PATH", conf)
    monkeypatch.setattr(PRManagerApp, "CONFIG_PATH", conf, raising=False)

    home = tmp_path / "home"
    repo_path = home / ".cache" / "gh_pr_manager" / "org/repo1"
    repo_path.mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: home)

    calls: list[list[str]] = []

    def fake_run(cmd, cwd=None):
        calls.append(cmd)
        if cmd[:4] == ["git", "-C", str(repo_path), "for-each-ref"]:
            return True, ""
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

    assert ["git", "-C", str(repo_path), "pull"] in calls
