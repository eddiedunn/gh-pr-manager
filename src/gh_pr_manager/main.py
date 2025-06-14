import json
from pathlib import Path

from .utils import run_cmd
from . import github_client
from textual.app import App, ComposeResult
from textual.widgets import (
    Header,
    Footer,
    Select,
    Button,
    Static,
)
from textual.containers import Container
from textual.css.query import NoMatches


class AuthScreen(Static):
    """Displayed when the GitHub CLI is not authenticated."""

    def compose(self) -> ComposeResult:
        yield Static(
            "Please run `gh auth login` in your terminal and restart the app.",
            id="auth_msg",
        )


CONFIG_PATH = Path(__file__).parent.parent / "config.json"

class RepoSelector(Static):
    """Temporary placeholder for repository selection."""

    def __init__(self, on_select):
        super().__init__()
        self.on_select = on_select

    def compose(self) -> ComposeResult:
        yield Static("Select repository (not implemented)", id="prompt")
        yield Button("Continue", id="continue")

    def on_button_pressed(self, event):
        if event.button.id == "continue":
            self.on_select("")


class BranchActions(Static):
    """Display branch actions like deletion or PR workflow."""

    def __init__(self, repo: str, branch_getter, refresh):
        super().__init__(id="branch_actions")
        self.repo = repo
        self.branch_getter = branch_getter
        self.refresh_callback = refresh

    def compose(self) -> ComposeResult:
        yield Button("Delete Branch", id="delete_branch")
        yield Button("PR/Merge/Delete", id="pr_flow")
        yield Static("", id="action_msg")

    def on_button_pressed(self, event) -> None:
        branch = self.branch_getter()
        msg = self.query_one("#action_msg")
        # Patch: handle NoSelection or None or non-string branch gracefully
        if not branch or not isinstance(branch, str):
            msg.update("No branch selected.")
            return

        if event.button.id == "delete_branch":
            success, output = run_cmd([
                "git",
                "-C",
                self.repo,
                "branch",
                "-D",
                branch,
            ])
            if success:
                msg.update(f"Deleted {branch}")
            else:
                msg.update(f"Delete failed: {output}")
        elif event.button.id == "pr_flow":
            success, output = run_cmd(
                ["gh", "pr", "create", "--fill", "--head", branch], cwd=self.repo
            )
            if not success:
                msg.update(f"Create failed: {output}")
                self.refresh_callback()
                return

            success, output = run_cmd(
                [
                    "gh",
                    "pr",
                    "merge",
                    "--merge",
                    "--delete-branch",
                    "--yes",
                ],
                cwd=self.repo,
            )
            if not success:
                msg.update(f"Merge failed: {output}")
                self.refresh_callback()
                return

            success, output = run_cmd(
                ["git", "-C", self.repo, "branch", "-D", branch]
            )
            if success:
                msg.update(f"PR merged and {branch} deleted")
            else:
                msg.update(f"Cleanup failed: {output}")

        self.refresh_callback()


class BranchSelector(Static):
    def __init__(self, repo: str, branches: list[str], on_back):
        super().__init__(id="branch_list")
        self.repo = repo
        self.branches = branches
        self.on_back = on_back

    def compose(self) -> ComposeResult:
        yield Static(f"Branches for {Path(self.repo).name}:")
        yield Select(options=[(b, b) for b in self.branches], id="branch_select")
        yield BranchActions(
            self.repo,
            lambda: self.query_one("#branch_select").value,
            self.refresh_branches,
        )
        yield Button("Back", id="back")

    def on_button_pressed(self, event) -> None:
        if event.button.id == "back":
            self.on_back()

    def refresh_branches(self) -> None:
        success, output = run_cmd(
            ["git", "-C", self.repo, "branch", "--format=%(refname:short)"]
        )
        if success:
            self.branches = [b.strip() for b in output.splitlines()]
        else:
            self.branches = []
        select = self.query_one("#branch_select")
        select.options = [(b, b) for b in self.branches]



class PRManagerApp(App):
    CSS_PATH = None
    BINDINGS = [ ("q", "quit", "Quit") ]

    def __init__(self):
        super().__init__()
        self.selected_repo = None

    def load_config(self):
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                self.selected_repo = json.load(f).get("selected_repository", "")
        else:
            self.selected_repo = ""

    def compose(self) -> ComposeResult:
        yield Header()
        if not github_client.check_auth_status():
            yield Container(AuthScreen(), id="main_container")
            yield Footer()
            return

        self.load_config()
        yield Container(
            RepoSelector(self.on_repo_selected),
            id="main_container",
        )
        yield Footer()


    def on_repo_selected(self, repo):
        self.selected_repo = repo
        container = self.query_one("#main_container")
        selector = container.query_one(RepoSelector)
        self.call_after_refresh(selector.remove)

        success, output = run_cmd(
            ["git", "-C", repo, "branch", "--format=%(refname:short)"]
        )
        if success:
            branches = [b.strip() for b in output.splitlines()]
        else:
            branches = []

        container.mount(BranchSelector(repo, branches, self.show_repo_selector))

    def show_repo_selector(self) -> None:
        container = self.query_one("#main_container")
        try:
            branch_list = container.query(BranchSelector).first()
            self.call_after_refresh(branch_list.remove)
        except NoMatches:
            pass
        container.remove_children()
        container.mount(RepoSelector(self.on_repo_selected))

if __name__ == "__main__":
    PRManagerApp().run()
