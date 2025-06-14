import json
import subprocess
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Select, Button, Static, Input
from textual.containers import Container

CONFIG_PATH = Path(__file__).parent.parent / "config.json"

class RepoSelector(Static):
    def __init__(self, repos, on_select):
        super().__init__()
        self.repos = repos
        self.on_select = on_select

    def compose(self) -> ComposeResult:
        yield Static("Select a repository:")
        yield Select(options=[(Path(r).name, r) for r in self.repos], id="repo_select")
        yield Button("Continue", id="continue")

    def on_button_pressed(self, event):
        repo = self.query_one("#repo_select").value
        self.on_select(repo)

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
        yield Container(RepoSelector(self.repositories, self.on_repo_selected))
        yield Footer()

    def on_repo_selected(self, repo):
        self.selected_repo = repo
        # TODO: Show branch selection UI
        self.exit(f"Selected repo: {repo}")

if __name__ == "__main__":
    PRManagerApp().run()
