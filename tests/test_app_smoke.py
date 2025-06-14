import pytest
from textual.app import App
from textual.pilot import Pilot
import json
import subprocess
from pathlib import Path

from gh_pr_manager import main
from gh_pr_manager.main import PRManagerApp, BranchList

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
        assert pilot.app.query_one(BranchList)
