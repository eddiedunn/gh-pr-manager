import pytest
from textual.app import App
from textual.pilot import Pilot
from gh_pr_manager.main import PRManagerApp

@pytest.mark.asyncio
async def test_app_runs():
    app = PRManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert pilot.app is not None
