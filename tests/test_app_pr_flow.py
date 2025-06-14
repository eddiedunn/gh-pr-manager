from gh_pr_manager import main
import json
import subprocess

import pytest

from gh_pr_manager.main import PRManagerApp


def _completed(cmd: list[str], returncode: int = 0, stdout: str = "", stderr: str = ""):
    return subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr=stderr)


@pytest.mark.asyncio
async def test_pr_flow_success(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "branch", "feature"], cwd=repo, check=True, capture_output=True)

    conf = tmp_path / "config.json"
    conf.write_text(json.dumps({"selected_repository": str(repo)}))
    monkeypatch.setattr(main, "CONFIG_PATH", conf)
    monkeypatch.setattr(PRManagerApp, "CONFIG_PATH", conf, raising=False)

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        if cmd[:4] == ["git", "-C", str(repo), "branch"] and "--format=%(refname:short)" in cmd:
            return _completed(cmd, stdout="main\nfeature\n")
        if cmd[:3] == ["gh", "pr", "create"]:
            return _completed(cmd)
        if cmd[:3] == ["gh", "pr", "merge"]:
            return _completed(cmd)
        if cmd[:4] == ["git", "-C", str(repo), "branch"] and "-D" in cmd:
            return _completed(cmd)
        return _completed(cmd)

    monkeypatch.setattr(subprocess, "run", fake_run)

    app = PRManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        pilot.app.on_owner_selected("org")
        await pilot.pause()
        pilot.app.on_repo_selected(str(repo))
        await pilot.pause()
        pilot.app.query_one("#branch_select").value = "feature"
        await pilot.click("#pr_flow")
        await pilot.pause()
        msg = pilot.app.query_one("#branch_list #action_msg").renderable

    assert "PR merged and feature deleted" in msg


@pytest.mark.asyncio
async def test_pr_flow_create_error(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "branch", "feature"], cwd=repo, check=True, capture_output=True)

    conf = tmp_path / "config.json"
    conf.write_text(json.dumps({"selected_repository": str(repo)}))
    monkeypatch.setattr(main, "CONFIG_PATH", conf)
    monkeypatch.setattr(PRManagerApp, "CONFIG_PATH", conf, raising=False)

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        if cmd[:4] == ["git", "-C", str(repo), "branch"] and "--format=%(refname:short)" in cmd:
            return _completed(cmd, stdout="main\nfeature\n")
        if cmd[:3] == ["gh", "pr", "create"]:
            return _completed(cmd, 1, stderr="create fail")
        if cmd[:4] == ["git", "-C", str(repo), "branch"] and "-D" in cmd:
            return _completed(cmd)
        return _completed(cmd)

    monkeypatch.setattr(subprocess, "run", fake_run)

    app = PRManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        pilot.app.on_owner_selected("org")
        await pilot.pause()
        pilot.app.on_repo_selected(str(repo))
        await pilot.pause()
        pilot.app.query_one("#branch_select").value = "feature"
        await pilot.click("#pr_flow")
        await pilot.pause()
        msg = pilot.app.query_one("#branch_list #action_msg").renderable

    assert "Create failed: create fail" in msg

