import json
import subprocess
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Select, Button, Static
from textual.containers import Container

CONFIG_PATH = Path(__file__).parent.parent / "config.json"

class RepoSelector(Static):
    def __init__(self, repos, on_select):
        super().__init__()
        self.repos = repos
        self.on_select = on_select

    def compose(self) -> ComposeResult:
        yield Static("Select a repository:", id="prompt")
        yield Select(options=[(Path(r).name, r) for r in self.repos], id="repo_select")
        yield Button("Continue", id="continue")
        confirm = Static("", id="confirm_text")
        confirm.display = False
        yield confirm
        confirm_btn = Button("Confirm", id="confirm")
        confirm_btn.display = False
        yield confirm_btn
        cancel_btn = Button("Cancel", id="cancel")
        cancel_btn.display = False
        yield cancel_btn

    def on_button_pressed(self, event):
        if event.button.id == "continue":
            repo = self.query_one("#repo_select").value
            if repo:
                self.selected_repo = repo
                confirm = self.query_one("#confirm_text")
                confirm.update(f"Use repository '{Path(repo).name}'?")
                confirm.display = True
                self.query_one("#confirm").display = True
                self.query_one("#cancel").display = True
        elif event.button.id == "confirm" and getattr(self, "selected_repo", None):
            self.on_select(self.selected_repo)
        elif event.button.id == "cancel":
            self.query_one("#confirm_text").display = False
            self.query_one("#confirm").display = False
            self.query_one("#cancel").display = False


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
        if not branch:
            msg.update("No branch selected.")
            return

        try:
            if event.button.id == "delete_branch":
                subprocess.run(
                    ["git", "-C", self.repo, "branch", "-D", branch],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                msg.update(f"Deleted {branch}")
            elif event.button.id == "pr_flow":
                subprocess.run(
                    ["gh", "pr", "create", "--fill", "--head", branch],
                    cwd=self.repo,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                subprocess.run(
                    ["gh", "pr", "merge", "--merge", "--delete-branch", "--yes"],
                    cwd=self.repo,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                subprocess.run(
                    ["git", "-C", self.repo, "branch", "-D", branch],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                msg.update(f"PR merged and {branch} deleted")
        except subprocess.CalledProcessError as e:
            msg.update(f"Action failed: {(e.stderr or e.stdout).strip()}")

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
        try:
            result = subprocess.run(
                ["git", "-C", self.repo, "branch", "--format=%(refname:short)"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.branches = [b.strip() for b in result.stdout.splitlines()]
        except subprocess.CalledProcessError:
            self.branches = []
        select = self.query_one("#branch_select")
        select.options = [(b, b) for b in self.branches]

class PRManagerApp(App):
    CSS_PATH = None
    BINDINGS = [ ("q", "quit", "Quit") ]

    def __init__(self):
        super().__init__()
        self.repositories = []
        self.selected_repo = None

    def load_config(self):
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                self.repositories = json.load(f)["repositories"]
        else:
            self.repositories = []

    def compose(self) -> ComposeResult:
        yield Header()
        self.load_config()
        yield Container(RepoSelector(self.repositories, self.on_repo_selected), id="main_container")
        yield Footer()

    def on_repo_selected(self, repo):
        self.selected_repo = repo
        container = self.query_one("#main_container")
        selector = container.query_one(RepoSelector)
        self.call_after_refresh(selector.remove)

        try:
            result = subprocess.run(
                ["git", "-C", repo, "branch", "--format=%(refname:short)"],
                capture_output=True,
                text=True,
                check=True,
            )
            branches = [b.strip() for b in result.stdout.splitlines()]
        except subprocess.CalledProcessError:
            branches = []

        container.mount(BranchSelector(repo, branches, self.show_repo_selector))

    def show_repo_selector(self) -> None:
        container = self.query_one("#main_container")
        branch_list = container.query_one(BranchSelector)
        self.call_after_refresh(branch_list.remove)
        container.mount(RepoSelector(self.repositories, self.on_repo_selected))

if __name__ == "__main__":
    PRManagerApp().run()
