import pytest
from textual.app import App

from gh_pr_manager.main import BranchActions
from gh_pr_manager import utils, main as main_module


class _BranchApp(App):
    def __init__(self, repo: str, branch: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repo = repo
        self.branch = branch

    def compose(self):
        yield BranchActions(self.repo, lambda: self.branch, lambda: None)


@pytest.mark.asyncio
async def test_delete_branch_command(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()

    calls: list[tuple[list[str], str | None]] = []

    def fake_run(cmd, cwd=None):
        calls.append((cmd, cwd))
        return True, ""

    monkeypatch.setattr(utils, "run_cmd", fake_run)
    monkeypatch.setattr(main_module, "run_cmd", fake_run)

    app = _BranchApp(str(repo), "feature")
    async with app.run_test() as pilot:
        await pilot.click("#delete_branch")
        await pilot.pause()
        msg = pilot.app.query_one("#action_msg").renderable

    assert ["git", "-C", str(repo), "push", "origin", "--delete", "feature"] in [c[0] for c in calls]
    assert "Deleted feature" in msg


@pytest.mark.asyncio
async def test_pr_flow_commands(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()

    calls: list[tuple[list[str], str | None]] = []

    def fake_run(cmd, cwd=None):
        calls.append((cmd, cwd))
        return True, ""

    monkeypatch.setattr(utils, "run_cmd", fake_run)
    monkeypatch.setattr(main_module, "run_cmd", fake_run)

    app = _BranchApp(str(repo), "feature")
    async with app.run_test() as pilot:
        await pilot.click("#pr_flow")
        await pilot.pause()
        msg = pilot.app.query_one("#action_msg").renderable

    expected = [
        ["gh", "pr", "create", "--fill", "--head", "feature"],
        ["gh", "pr", "merge", "--merge", "--delete-branch", "--yes"],
        ["git", "-C", str(repo), "branch", "-D", "feature"],
    ]
    for exp in expected:
        assert exp in [c[0] for c in calls]
    assert "PR merged and feature deleted" in msg
