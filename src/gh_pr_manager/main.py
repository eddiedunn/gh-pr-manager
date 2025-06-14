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
    Input,
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


class OrgSelector(Static):
    """Widget for choosing a GitHub organization or user account."""

    def __init__(self, on_select):
        super().__init__(id="org_selector")
        self.on_select = on_select

    def compose(self) -> ComposeResult:
        yield Static("Select an organization:")
        yield Select(options=[], id="org_select")
        yield Button("Continue", id="org_continue")

    def on_mount(self) -> None:
        login = github_client.get_user_login() or ""
        orgs = github_client.get_user_orgs()
        options = [(login, login)] if login else []
        options += [(org, org) for org in orgs]
        self.query_one("#org_select").options = options

    def on_button_pressed(self, event) -> None:
        if event.button.id == "org_continue":
            owner = self.query_one("#org_select").value
            if owner:
                self.on_select(owner)


class RepoSelectionWidget(Static):
    """Widget for selecting a repository from the chosen owner."""

    def __init__(self, owner: str, on_select):
        super().__init__(id="repo_selector")
        self.owner = owner
        self.on_select = on_select
        self.repos: list[str] = []

    def compose(self) -> ComposeResult:
        yield Static(f"Repositories for {self.owner}")
        yield Input(placeholder="Filter", id="repo_filter")
        yield Select(options=[], id="repo_select")
        yield Static("Loading...", id="repo_loading")
        yield Button("Select", id="repo_continue")

    def on_mount(self) -> None:
        repos = github_client.get_repos(self.owner)
        self.repos = repos
        select = self.query_one("#repo_select")
        select.options = [(r, r) for r in repos]
        self.query_one("#repo_loading").remove()

    def on_input_changed(self, event: Input.Changed) -> None:
        term = event.value.lower()
        filtered = [(r, r) for r in self.repos if term in r.lower()]
        self.query_one("#repo_select").options = filtered

    def on_button_pressed(self, event) -> None:
        if event.button.id == "repo_continue":
            repo = self.query_one("#repo_select").value
            if repo:
                self.on_select(repo)


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
            success, output = run_cmd(
                [
                    "git",
                    "-C",
                    self.repo,
                    "push",
                    "origin",
                    "--delete",
                    branch,
                ]
            )
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
        run_cmd(["git", "-C", self.repo, "fetch", "--prune"])
        success, output = run_cmd(
            [
                "git",
                "-C",
                self.repo,
                "for-each-ref",
                "--format=%(refname:short)",
                "refs/remotes/origin/",
            ]
        )
        if success:
            lines = [l.strip() for l in output.splitlines()]
            self.branches = [
                l.replace("origin/", "", 1)
                for l in lines
                if l and not l.startswith("origin/HEAD")
            ]
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
            OrgSelector(self.on_owner_selected),
            id="main_container",
        )
        yield Footer()


    def on_owner_selected(self, owner: str) -> None:
        container = self.query_one("#main_container")
        selector = container.query_one(OrgSelector)
        self.call_after_refresh(selector.remove)
        container.mount(RepoSelectionWidget(owner, self.on_repo_selected))

    def on_repo_selected(self, repo: str) -> None:
        self.selected_repo = repo
        # Persist selection
        with open(CONFIG_PATH, "w") as f:
            json.dump({"selected_repository": repo}, f)

        container = self.query_one("#main_container")
        selector = container.query_one(RepoSelectionWidget)
        self.call_after_refresh(selector.remove)

        clone_base = Path.home() / ".cache" / "gh_pr_manager"
        repo_path = clone_base / repo
        if not repo_path.exists():
            repo_path.parent.mkdir(parents=True, exist_ok=True)
            run_cmd(["gh", "repo", "clone", repo, str(repo_path)])
        else:
            run_cmd(["git", "-C", str(repo_path), "pull"])

        run_cmd(["git", "-C", str(repo_path), "fetch", "--prune"])
        success, output = run_cmd(
            [
                "git",
                "-C",
                str(repo_path),
                "for-each-ref",
                "--format=%(refname:short)",
                "refs/remotes/origin/",
            ]
        )
        if success:
            lines = [l.strip() for l in output.splitlines()]
            branches = [
                l.replace("origin/", "", 1)
                for l in lines
                if l and not l.startswith("origin/HEAD")
            ]
        else:
            branches = []

        container.mount(
            BranchSelector(str(repo_path), branches, self.show_repo_selector)
        )

    def show_repo_selector(self) -> None:
        container = self.query_one("#main_container")
        try:
            branch_list = container.query(BranchSelector).first()
            self.call_after_refresh(branch_list.remove)
        except NoMatches:
            pass
        container.remove_children()
        container.mount(RepoSelectionWidget(self.selected_repo.split("/")[0], self.on_repo_selected))

if __name__ == "__main__":
    PRManagerApp().run()
