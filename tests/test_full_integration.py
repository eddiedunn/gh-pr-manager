import pytest
import json
import subprocess
from pathlib import Path
from gh_pr_manager import main
from gh_pr_manager.main import PRManagerApp, BranchSelector, RepoSelector

@pytest.mark.asyncio
async def test_select_repo_with_no_branches(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    # No branches except main
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=repo, check=True, capture_output=True)
    conf = tmp_path / "config.json"
    conf.write_text(json.dumps({"selected_repository": str(repo)}))
    monkeypatch.setattr(main, "CONFIG_PATH", conf)
    app = PRManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        pilot.app.on_repo_selected(str(repo))
        await pilot.pause()
        sel = pilot.app.query_one(BranchSelector)
        assert sel is not None
        select = pilot.app.query_one("#branch_select")
        # Accept the blank option as the first entry
        assert select._options[0] == ("", select.BLANK)
        branch_name = select._options[1][0]
        assert branch_name in {"main", "master"}

@pytest.mark.asyncio
async def test_try_pr_with_no_branch_selected(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "branch", "feature"], cwd=repo, check=True, capture_output=True)
    conf = tmp_path / "config.json"
    conf.write_text(json.dumps({"selected_repository": str(repo)}))
    monkeypatch.setattr(main, "CONFIG_PATH", conf)
    app = PRManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        pilot.app.on_repo_selected(str(repo))
        await pilot.pause()
        select = pilot.app.query_one("#branch_select")
        select.clear()
        await pilot.click("#pr_flow")
        await pilot.pause()
        msg = pilot.app.query_one("#branch_list #action_msg").renderable
        assert "No branch selected" in msg

@pytest.mark.skip("repo editing removed")
@pytest.mark.asyncio
async def test_edit_repos_add_and_remove(tmp_path, monkeypatch):
    repo1 = tmp_path / "repo1"
    repo2 = tmp_path / "repo2"
    repo1.mkdir()
    repo2.mkdir()
    conf = tmp_path / "config.json"
    conf.write_text(json.dumps({"selected_repository": str(repo1)}))
    monkeypatch.setattr(main, "CONFIG_PATH", conf)
    app = PRManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.click("#edit_repos")
        await pilot.pause()
        pilot.app.query_one("#new_repo_input").value = str(repo2)
        await pilot.click("#add_repo")
        await pilot.click("#save_repos")
        await pilot.pause()
        # Now remove repo1
        await pilot.click("#edit_repos")
        await pilot.pause()
        cb = pilot.app.query_one("#repo_cb_0")
        cb.value = True  # simulate unchecking
        await pilot.click("#save_repos")
        await pilot.pause()
        # Check config file
        config = json.loads(conf.read_text())
        assert config.get("selected_repository") == str(repo2)

@pytest.mark.asyncio
async def test_keyboard_navigation_and_quit(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=repo, check=True, capture_output=True)
    conf = tmp_path / "config.json"
    conf.write_text(json.dumps({"selected_repository": str(repo)}))
    monkeypatch.setattr(main, "CONFIG_PATH", conf)
    app = PRManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("tab")
        await pilot.press("tab")
        await pilot.press("q")
        # App should quit without error

@pytest.mark.skip("repo editing removed")
@pytest.mark.asyncio
async def test_config_persistence(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    conf = tmp_path / "config.json"
    conf.write_text(json.dumps({"selected_repository": str(repo)}))
    monkeypatch.setattr(main, "CONFIG_PATH", conf)
    app = PRManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.click("#edit_repos")
        await pilot.pause()
        pilot.app.query_one("#new_repo_input").value = str(repo)
        await pilot.click("#add_repo")
        await pilot.click("#save_repos")
        await pilot.pause()
    # Restart app and check config
    app2 = PRManagerApp()
    app2.load_config()
    assert app2.selected_repo == str(repo)
