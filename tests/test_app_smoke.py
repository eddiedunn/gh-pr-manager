import pytest
from textual.app import App
from textual.pilot import Pilot
import json
import subprocess
from pathlib import Path

from gh_pr_manager import main
from gh_pr_manager.main import PRManagerApp, BranchSelector
from gh_pr_manager import utils
from gh_pr_manager import github_client

@pytest.mark.asyncio
async def test_app_runs():
    app = PRManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert pilot.app is not None


@pytest.mark.asyncio
async def test_auth_screen_shown_when_not_logged_in(monkeypatch):
    monkeypatch.setattr(github_client, "check_auth_status", lambda: False)
    app = PRManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert pilot.app.query_one("#auth_msg")


@pytest.mark.asyncio
async def test_select_repo_shows_branches(tmp_path, monkeypatch):
    conf = tmp_path / "config.json"
    conf.write_text(json.dumps({"selected_repository": ""}))
    monkeypatch.setattr(main, "CONFIG_PATH", conf)

    app = PRManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        pilot.app.on_owner_selected("org")
        await pilot.pause()
        pilot.app.on_repo_selected("org/repo")
        await pilot.pause()
        assert pilot.app.query_one(BranchSelector)


@pytest.mark.asyncio
async def test_delete_branch_runs_git(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run([
        "git",
        "commit",
        "--allow-empty",
        "-m",
        "init",
    ], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "branch", "feature"], cwd=repo, check=True, capture_output=True)

    conf = tmp_path / "config.json"
    conf.write_text(json.dumps({"selected_repository": str(repo)}))
    monkeypatch.setattr(main, "CONFIG_PATH", conf)

    repo_clone = Path.home() / ".cache" / "gh_pr_manager" / str(repo)
    calls = []

    def fake_run_cmd(cmd, cwd=None):
        calls.append(cmd)
        if cmd[:4] == ["git", "-C", str(repo_clone), "fetch"]:
            return True, ""
        if cmd[:4] == ["git", "-C", str(repo_clone), "for-each-ref"]:
            return True, "origin/main\norigin/feature\n"
        return True, ""

    monkeypatch.setattr(utils, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(main, "run_cmd", fake_run_cmd)

    app = PRManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        pilot.app.on_owner_selected("org")
        await pilot.pause()
        pilot.app.on_repo_selected(str(repo))
        await pilot.pause()
        pilot.app.query_one("#branch_select").value = "feature"
        await pilot.click("#delete_branch")
        await pilot.pause()

    assert [
        "git",
        "-C",
        str(repo_clone),
        "push",
        "origin",
        "--delete",
        "feature",
    ] in calls


@pytest.mark.skip("repo editing removed")
@pytest.mark.asyncio
async def test_edit_repositories_updates_config(tmp_path, monkeypatch):
    repo1 = tmp_path / "r1"
    repo1.mkdir()
    repo2 = tmp_path / "r2"
    repo2.mkdir()

    conf = tmp_path / "config.json"
    conf.write_text(json.dumps({"selected_repository": str(repo1)}))
    monkeypatch.setattr(main, "CONFIG_PATH", conf)

    new_repo = tmp_path / "r3"
    new_repo.mkdir()

    app = PRManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.click("#edit_repos")
        pilot.app.query_one("#new_repo_input").value = str(new_repo)
        await pilot.click("#add_repo")
        await pilot.click("#repo_cb_0")
        await pilot.click("#save_repos")
        await pilot.pause()

        select = pilot.app.query_one("#repo_select")
        options = [opt[1] for opt in select._options[1:]]

    data = json.loads(conf.read_text())
    assert data["selected_repository"] == str(new_repo)
    assert options == []


@pytest.mark.skip("repo validation removed")
@pytest.mark.asyncio
async def test_invalid_repo_shows_message(tmp_path, monkeypatch):
    repo = tmp_path / "valid"
    repo.mkdir()
    bad_repo = tmp_path / "missing"

    conf = tmp_path / "config.json"
    conf.write_text(json.dumps({"selected_repository": str(repo)}))
    monkeypatch.setattr(main, "CONFIG_PATH", conf)

    app = PRManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        msg = pilot.app.query_one("#invalid_msg")
        assert "missing" in msg.renderable
        select = pilot.app.query_one("#repo_select")
        options = [opt[1] for opt in select._options[1:]]
        assert str(repo) in options
        assert str(bad_repo) not in options
