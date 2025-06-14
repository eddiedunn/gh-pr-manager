import pytest
from textual.app import App
from textual.pilot import Pilot
import json
import subprocess
from pathlib import Path

from gh_pr_manager import main
from gh_pr_manager.main import PRManagerApp, BranchSelector

@pytest.mark.asyncio
async def test_app_runs():
    app = PRManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert pilot.app is not None


@pytest.mark.asyncio
async def test_select_repo_shows_branches(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "branch", "feature"], cwd=repo, check=True, capture_output=True)

    conf = tmp_path / "config.json"
    conf.write_text(json.dumps({"repositories": [str(repo)]}))
    monkeypatch.setattr(main, "CONFIG_PATH", conf)

    app = PRManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        pilot.app.query_one("#repo_select").value = str(repo)
        await pilot.click("#continue")
        await pilot.click("#confirm")
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
    conf.write_text(json.dumps({"repositories": [str(repo)]}))
    monkeypatch.setattr(main, "CONFIG_PATH", conf)

    calls = []

    def fake_run(cmd, *a, **kw):
        calls.append(cmd)
        class R:
            stdout = ""
            stderr = ""

        if cmd[:4] == ["git", "-C", str(repo), "branch"] and "--format=%(refname:short)" in cmd:
            R.stdout = "main\nfeature\n"
        return R

    monkeypatch.setattr(subprocess, "run", fake_run)

    app = PRManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        pilot.app.query_one("#repo_select").value = str(repo)
        await pilot.click("#continue")
        await pilot.click("#confirm")
        await pilot.pause()
        pilot.app.query_one("#branch_select").value = "feature"
        await pilot.click("#delete_branch")
        await pilot.pause()

    assert ["git", "-C", str(repo), "branch", "-D", "feature"] in calls


@pytest.mark.asyncio
async def test_edit_repositories_updates_config(tmp_path, monkeypatch):
    repo1 = tmp_path / "r1"
    repo1.mkdir()
    repo2 = tmp_path / "r2"
    repo2.mkdir()

    conf = tmp_path / "config.json"
    conf.write_text(json.dumps({"repositories": [str(repo1), str(repo2)]}))
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
    assert data["repositories"] == [str(repo2), str(new_repo)]
    assert options == [str(repo2), str(new_repo)]
