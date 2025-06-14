import json
import subprocess
from pathlib import Path

import pytest
from textual.app import App

from gh_pr_manager import main
from gh_pr_manager.main import BranchActions


class _BranchApp(App):
    def __init__(self, repo: str, branch: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repo = repo
        self.branch = branch

    def compose(self):
        yield BranchActions(self.repo, lambda: self.branch, lambda: None)


def _completed(cmd: list[str], returncode: int = 0, stdout: str = "", stderr: str = ""):
    return subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr=stderr)


def test_load_config_reads_selected_repo(tmp_path, monkeypatch):
    conf = tmp_path / "config.json"
    conf.write_text(json.dumps({"selected_repository": "example/repo"}))
    monkeypatch.setattr(main, "CONFIG_PATH", conf)

    app = main.PRManagerApp()
    app.load_config()
    assert app.selected_repo == "example/repo"


@pytest.mark.asyncio
async def test_branch_actions_delete_branch(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()

    calls = []

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        calls.append(cmd)
        if cmd[:4] == ["git", "-C", str(repo), "push"] and "--delete" in cmd:
            return _completed(cmd)
        return _completed(cmd)

    monkeypatch.setattr(subprocess, "run", fake_run)

    app = _BranchApp(str(repo), "feature")
    async with app.run_test() as pilot:
        await pilot.click("#delete_branch")
        await pilot.pause()
        msg = pilot.app.query_one("#action_msg").renderable

    assert ["git", "-C", str(repo), "push", "origin", "--delete", "feature"] in calls
    assert "Deleted feature" in msg


@pytest.mark.asyncio
async def test_branch_actions_pr_flow_create_fail(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        if cmd[:3] == ["gh", "pr", "create"]:
            return _completed(cmd, 1, stderr="create fail")
        return _completed(cmd)

    monkeypatch.setattr(subprocess, "run", fake_run)

    app = _BranchApp(str(repo), "feature")
    async with app.run_test() as pilot:
        await pilot.click("#pr_flow")
        await pilot.pause()
        msg = pilot.app.query_one("#action_msg").renderable

    assert "Create failed: create fail" in msg
