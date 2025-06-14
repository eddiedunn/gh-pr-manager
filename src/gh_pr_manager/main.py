import json
from pathlib import Path

from .utils import run_cmd, filter_valid_repos
from textual.app import App, ComposeResult
from textual.widgets import (
    Header,
    Footer,
    Select,
    Button,
    Static,
    Input,
    Checkbox,
)
from textual.containers import Container
from textual.css.query import NoMatches

CONFIG_PATH = Path(__file__).parent.parent / "config.json"

class RepoSelector(Static):
    def __init__(self, repos, on_select, on_edit, invalid=None):
        super().__init__()
        self.repos = repos
        self.on_select = on_select
        self.on_edit = on_edit
        self.invalid = invalid or []

    def compose(self) -> ComposeResult:
        if self.invalid:
            removed = ", ".join(Path(r).name for r in self.invalid)
            yield Static(
                f"Removed invalid repos: {removed}. Please edit your config.",
                id="invalid_msg",
            )
        yield Static("Select a repository:", id="prompt")
        yield Select(options=[(Path(r).name, r) for r in self.repos], id="repo_select")
        yield Button("Continue", id="continue")
        yield Button("Edit Repositories", id="edit_repos")
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
        elif event.button.id == "edit_repos":
            self.on_edit()
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


class RepoEditor(Static):
    """Widget for adding/removing repositories."""

    def __init__(self, repos: list[str], on_save, on_cancel):
        super().__init__(id="repo_editor")
        self.repos = repos
        self.on_save = on_save
        self.on_cancel = on_cancel

    def compose(self) -> ComposeResult:
        yield Static("Edit repositories:")
        yield Container(
            *[Checkbox(repo, id=f"repo_cb_{i}") for i, repo in enumerate(self.repos)],
            id="repo_checks",
        )
        yield Input(placeholder="New repo path", id="new_repo_input")
        yield Button("Add", id="add_repo")
        yield Button("Save", id="save_repos")
        yield Button("Cancel", id="cancel_edit")

    def on_button_pressed(self, event) -> None:
        if event.button.id == "add_repo":
            new_repo = self.query_one("#new_repo_input").value.strip()
            if new_repo:
                self.query_one("#repo_checks").mount(Checkbox(new_repo))
                self.query_one("#new_repo_input").value = ""
        elif event.button.id == "save_repos":
            repos = [
                str(cb.label)
                for cb in self.query("#repo_checks Checkbox")
                if not cb.value
            ]
            self.on_save(repos)
        elif event.button.id == "cancel_edit":
            self.on_cancel()

class PRManagerApp(App):
    CSS_PATH = None
    BINDINGS = [ ("q", "quit", "Quit") ]

    def __init__(self):
        super().__init__()
        self.repositories = []
        self.selected_repo = None
        self.invalid_repos: list[str] = []

    def load_config(self):
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                self.repositories = json.load(f)["repositories"]
        else:
            self.repositories = []
        self.repositories, self.invalid_repos = filter_valid_repos(self.repositories)

    def compose(self) -> ComposeResult:
        yield Header()
        self.load_config()
        yield Container(
            RepoSelector(
                self.repositories,
                self.on_repo_selected,
                self.open_repo_editor,
                self.invalid_repos,
            ),
            id="main_container",
        )
        yield Footer()

    def save_repositories(self, repos: list[str]) -> None:
        self.repositories, self.invalid_repos = filter_valid_repos(repos)
        with open(CONFIG_PATH, "w") as f:
            json.dump({"repositories": self.repositories}, f, indent=4)
        self.show_repo_selector()

    def open_repo_editor(self) -> None:
        container = self.query_one("#main_container")
        selector = container.query_one(RepoSelector)
        self.call_after_refresh(selector.remove)
        container.mount(
            RepoEditor(self.repositories, self.save_repositories, self.show_repo_selector)
        )

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
        try:
            editor = container.query(RepoEditor).first()
            self.call_after_refresh(editor.remove)
        except NoMatches:
            pass
        container.mount(
            RepoSelector(
                self.repositories,
                self.on_repo_selected,
                self.open_repo_editor,
                self.invalid_repos,
            )
        )

if __name__ == "__main__":
    PRManagerApp().run()
