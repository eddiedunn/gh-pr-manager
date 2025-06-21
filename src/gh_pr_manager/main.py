import json
import logging
import re
import traceback
from pathlib import Path

from . import github_client
from .utils import run_cmd
from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.css.query import NoMatches
from textual.message import Message
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Select,
    Static,
)


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
        print("DEBUG: OrgSelector.__init__")
        super().__init__(id="org_selector")
        self.on_select = on_select

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        print(f"DEBUG: OrgSelector.on_button_pressed called, button.id={getattr(event.button, 'id', None)}")
        children = list(self.children)
        print(f"DEBUG: OrgSelector children at button press: {[type(child).__name__ for child in children]}")
        if event.button.id == "org_continue":
            select = self.query_one("#org_select", expect_type=Select, default=None)
            selected = select.value if select else None
            print(f"DEBUG: OrgSelector.on_button_pressed - selected={selected}")
            if selected and self.on_select:

    def compose(self) -> ComposeResult:
        print("DEBUG: OrgSelector.compose")
        yield Horizontal(
            Select(
                *[(org, org) for org in self.orgs],
                id="org_select",
                prompt="Select an owner..."
            ) if len(self.orgs) > 1 else Static(f"Owner: {self.orgs[0]}", id="org_only"),
            Button("Continue", id="org_continue")
        )

    async def on_mount(self) -> None:
        print("DEBUG: OrgSelector.on_mount")
        login = (github_client.get_user_login() or "").strip()
        orgs = [org.strip() for org in github_client.get_user_orgs() if org.strip()]
        options = []
        if login:
            options.append((login, login))
        options.extend((org, org) for org in orgs)
        loading = self.query_one("#org_loading")
        loading.remove()
        from textual.widgets import Select
        if len(options) > 1:
            select = Select(options=options, id="org_select", allow_blank=False, prompt="Choose an owner...")
            await self.mount(select, before="#org_continue")
        elif len(options) == 1:
            await self.mount(Static(f"Owner: {options[0][0]}", id="org_only"), before="#org_continue")
        else:
            await self.mount(Static("No owners found", id="org_none"), before="#org_continue")
        import logging
        logging.basicConfig(filename="org_selector_debug.log", level=logging.INFO, filemode="a")
        logging.info(f"DEBUG OrgSelector (final): login={login!r} orgs={orgs!r} options={options!r}")



    def on_button_pressed(self, event) -> None:
        import logging
        logging.basicConfig(filename="org_selector_debug.log", level=logging.INFO, filemode="a")
        if event.button.id == "org_continue":
            owner = None
            try:
                select = self.query_one("#org_select")
                owner = select.value
            except Exception:
                try:
                    static_owner = self.query_one("#org_only")
                    # Try to extract text robustly
                    try:
                        text = static_owner.renderable.text
                    except AttributeError:
                        text = str(static_owner.renderable)
                    owner = text.replace("Owner: ", "").strip()
                except Exception:
                    pass
            logging.info(f"DEBUG on_button_pressed: owner={owner!r}")
            if owner:
                self.on_select(owner)
            else:
                logging.info("DEBUG on_button_pressed: No owner selected!")


class RepoSelectionWidget(Static):
    """Widget for selecting a repository from the chosen owner."""
    def __init__(self, owner: str, on_select=None, **kwargs):
        print(f"DEBUG: RepoSelectionWidget.__init__ for owner={owner}")
        super().__init__(**kwargs)
        self.owner = owner
        self.on_select = on_select
        self.repos = []
        self.filtered_repos = []
        self.loading = True
        self._initialized = False
        self._list_view = None  # Strong reference to the list view widget

    def compose(self) -> ComposeResult:
        print("DEBUG: RepoSelectionWidget.compose")
        with Vertical():
            yield Static("DEBUG: UI reached here", id="debug_top")
            yield Static(f"Repositories for {self.owner}")
            yield Input(placeholder="Filter repositories...", id="repo_filter")
            yield Static("Loading repositories...", id="repo_loading")
            yield ListView(id="repo_list")

    async def on_mount(self) -> None:
        print("DEBUG: RepoSelectionWidget.on_mount")
        try:
            logging.info(f"Mounting repo selector for owner: {self.owner}")
            # ... your code here ...
        except Exception as e:
            print(f"Error in RepoSelectionWidget.on_mount: {e}")
            logging.error(f"Error in RepoSelectionWidget.on_mount: {e}")
                
    def _finish_initialization(self):
        """Complete the initialization after the list view is found."""
        try:
            logging.info(f"List view initialized: {self._list_view}")
            # ... your code here ...
        except Exception as e:
            print(f"Error in _finish_initialization: {e}")
            logging.error(f"Error in _finish_initialization: {e}")
        
            # Set up event handlers
            filter_input = self.query_one("#repo_filter")
            if filter_input:
                filter_input.on_change = self.on_input_changed
            else:
                logging.error("Failed to find #repo_filter")
                return
            
            # Mark as initialized
            self._initialized = True
            
            # Fetch repositories in a background task to keep the UI responsive
            self.run_worker(self._load_repositories())
            
        except Exception as e:
            error_msg = f"Error in _finish_initialization: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            self.notify(error_msg, severity="error")
    
    async def _load_repositories(self) -> None:
        """Load repositories asynchronously."""
        print(f"DEBUG: _load_repositories called for owner={self.owner}")
        # Simulate async repo loading for now
        import asyncio
        from types import SimpleNamespace
        await asyncio.sleep(0.1)
        # Replace with real GitHub API call or gh CLI integration
        self.repos = [SimpleNamespace(name=f"repo-{i}") for i in range(3)]
        print(f"DEBUG: _load_repositories loaded repos: {[r.name for r in self.repos]}")
        self.filtered_repos = list(self.repos)
        self.update_list_view()
        # Update the UI on the main thread
        self.call_after_refresh(
            self._on_repositories_loaded,
            self.repos
        )
            
    def _update_repo_list(self, repos: list[str]) -> None:
        """Update the repository list in the UI."""
        try:
            # Update widget state
            self.repos = repos
            self.filtered_repos = repos.copy()
            
            # Update the list view
            self.update_list_view(self.filtered_repos)
            
            # Remove loading message
            loading = self.query_one("#repo_loading")
            if loading:
                loading.remove()
            
            # Set focus to the list view
            if self.list_view:
                self.list_view.focus()
                
            logging.info("Repository list updated successfully")
            
        except Exception as e:
            error_msg = f"Failed to update repository list: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            self.notify(f"Error updating repository list: {e}", severity="error")

    def log_widget_tree(self, widget=None, indent=0):
        """Recursively log the widget tree for debugging"""
        if widget is None:
            widget = self
            logging.info("\n=== WIDGET TREE ===")
            
        widget_id = f"{widget.__class__.__name__}(id={getattr(widget, 'id', 'N/A')})"
        logging.info("  " * indent + f"- {widget_id}")
        
        if hasattr(widget, 'children'):
            for child in widget.children:
                self.log_widget_tree(child, indent + 1)
                
        if widget is self:
            logging.info("=== END WIDGET TREE ===\n")

    def on_input_changed(self, event: Input.Changed) -> None:
        term = event.value.lower()
        self.filtered_repos = [r for r in self.repos if term in r.name.lower()]
        self.update_list_view()

    def _on_repositories_loaded(self, repos):
        """Handle repositories loaded event.

        Args:
            repos: List of repository objects or an exception if loading failed
        """
        if isinstance(repos, Exception):
            error_msg = f"Error loading repositories: {str(repos)}"
            logging.error(error_msg)
            self.notify(error_msg, severity="error")
            return

        try:
            self.repos = repos
            self.filtered_repos = list(repos)  # Initialize filtered list
            logging.info(f"Found {len(repos)} repositories for {self.owner}")

            # Ensure we have a valid list view reference
            if self._list_view is None:
                logging.warning("List view reference lost, trying to find it...")
                self._list_view = self.query_one("#repo_list")

            if self._list_view is None:
                logging.error("Could not find list view after repository load")
                return

            # Update the UI with the repositories
            self.call_after_refresh(self.update_list_view)

        except Exception as e:
            error_msg = f"Error handling repositories: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            self.notify(error_msg, severity="error")

    def update_list_view(self, repos=None):
        """Update the list view with repositories.

        Args:
            repos: Optional list of repositories to display. If None, uses self.filtered_repos
        """
        try:
            if self._list_view is None:
                logging.error("List view reference is None in update_list_view")
                return
            # Use provided repos or fall back to filtered_repos
            repos_to_display = repos if repos is not None else getattr(self, 'filtered_repos', [])
            if not repos_to_display:
                logging.warning("No repositories to display in update_list_view")
                self._list_view.clear()
                try:
                    debug_label = self.query_one("#repo_debug_label")
                    debug_label.update("[debug] No repos to display.")
                except Exception:
                    pass
                return
            # Clear the list view and add new items
            self._list_view.clear()
            for repo in repos_to_display:
                repo_name = repo.name if hasattr(repo, 'name') else str(repo)
                self._list_view.append(ListItem(Label(repo_name)))
            try:
                debug_label = self.query_one("#repo_debug_label")
                debug_label.update(f"[debug] Repo list updated with {len(repos_to_display)} items.")
            except Exception:
                pass
            logging.info(f"Repository list updated successfully with {len(repos_to_display)} items")
            # Add timer to log number of items in ListView after update
            from threading import Timer
            def log_listview_count():
                try:
                    count = len(self._list_view.children)
                    logging.info(f"[timer] ListView now has {count} children after update_list_view")
                except Exception as e:
                    logging.error(f"[timer] Error logging ListView count: {e}")
            Timer(2.0, log_listview_count).start()
        except Exception as e:
            error_msg = f"Error in update_list_view: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            self.notify(error_msg, severity="error")

    def on_list_view_selected(self, event):
        """Handle repository selection from the list"""
        try:
            item = event.item if hasattr(event, 'item') else None
            if not item or not hasattr(item, 'children') or not item.children:
                logging.warning("No valid item selected")
                return
                
            # Get the label from the selected item
            label = item.children[0]
            repo = None
            
            # Extract the repository name from the label
            if hasattr(label, 'renderable') and isinstance(label.renderable, str):
                repo = label.renderable
            elif hasattr(label, 'plain'):
                repo = label.plain
            elif hasattr(label, 'text'):
                repo = label.text
                
            if repo:
                logging.info(f"Repository selected: {repo}")
                self.on_select(repo)
            else:
                logging.warning("Could not determine selected repository")
                
        except Exception as e:
            logging.error(f"Error in on_list_view_selected: {str(e)}")
            logging.error(traceback.format_exc())




class BranchActions(Static):
    """Display branch actions like deletion or PR workflow."""

    def __init__(self, repo, multi_branch_getter, refresh_callback):
        super().__init__()
        self.repo = repo
        self.multi_branch_getter = multi_branch_getter  # returns set/list of selected branches
        self.refresh_callback = refresh_callback

    def compose(self) -> ComposeResult:
        yield Label("", id="action_msg")
        yield Button("Delete Branch", id="delete_branch")
        yield Button("PR/Merge/Delete", id="pr_flow")

    def on_button_pressed(self, event) -> None:
        branches = self.multi_branch_getter()
        msg = self.query_one("#action_msg")
        if not branches:
            msg.update("No branch selected.")
            return
        if event.button.id == "delete_branch":
            if len(branches) > 1:
                # Multi-branch delete confirmation should be handled by parent (BranchSelector)
                self.app.post_message("multi_delete_requested")
            else:
                branch = next(iter(branches))
                success, output = run_cmd(["git", "-C", self.repo, "branch", "-D", branch])
                if success:
                    msg.update(f"Deleted {branch}")
                    self.set_timer(2, lambda: msg.update(""))
                    self.refresh_callback()
                else:
                    msg.update(f"Delete failed: {output}")
        elif event.button.id == "pr_flow":
            if len(branches) > 1:
                msg.update("Select only one branch for PR/Merge/Delete.")
                self.set_timer(2, lambda: msg.update(""))
                return
            branch = next(iter(branches))
            # PR/Merge/Delete logic as before
            success, output = run_cmd(["gh", "pr", "create", "--repo", self.repo, "--head", branch, "--base", "main", "--title", branch, "--body", "Automated PR"])
            if not success:
                msg.update(f"Create failed: {output}")
                self.refresh_callback()
                return
            success, output = run_cmd(["gh", "pr", "merge", "--repo", self.repo, "--head", branch, "--delete-branch", "--yes"])
            if not success:
                msg.update(f"Merge failed: {output}")
                self.refresh_callback()
                return
            success, output = run_cmd(["git", "-C", self.repo, "branch", "-D", branch])
            if success:
                msg.update(f"PR merged and {branch} deleted")
                self.set_timer(2, lambda: msg.update(""))
                self.refresh_callback()  # Refresh the branch list immediately
            else:
                msg.update(f"Cleanup failed: {output}")

        # self.refresh_callback()  # Removed this line to avoid duplicate refresh
class BranchSelector(Static):
    class BranchSelectionChanged(Message):
        def __init__(self, selected):
            self.selected = selected
            super().__init__()

    def __init__(self, repo: str, branches: list[str], on_back):
        super().__init__(id="branch_list")
        self.repo = repo
        self.branches = branches
        self.on_back = on_back
        self.selected_branches = set()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        
        # Main container with quit button overlay
        with Container(id="main_container"):
            yield Static("", id="content")
            yield QuitButton(id="quit_button")
            
            # Main container with border for visual separation
            with Container(classes="main-container"):
                # Header with repo name
                yield Static(f"[b]Repository:[/b] {Path(self.repo).name}", classes="header")
                
                # Action buttons in a horizontal row
                with Horizontal(classes="button-row"):
                    yield Button("Delete Branch", id="delete_branch", classes="action-btn")
                    yield Button("PR/Merge/Delete", id="pr_flow", classes="action-btn")
                    yield Button("🔄 Refresh", id="refresh", classes="action-btn")
                
                # Status message
                self.msg_label = Static("Click to select/deselect branches", classes="hint")
                yield self.msg_label
                
                # Main branch list taking up remaining space
                with Container(classes="list-container"):
                    self.list_view = ListView(id="branch_listview")
                    yield self.list_view
                
                # Footer with back button
                with Horizontal(classes="footer"):
                    yield Static("", classes="filler")
                    yield Button("← Back to Repositories", id="back", variant="primary")

        yield Footer()
        
    def on_mount(self) -> None:
        """Set up the app after the DOM is ready."""
        # Position the quit button in the top-right corner
        quit_btn = self.query_one("#quit_button")
        quit_btn.styles.offset = ("100vw - 10", 1)
        quit_btn.styles.layer = "overlay"
        
        self.list_view = self.query_one("#branch_listview")
        self.populate_list_view()
        self.update_buttons()


class BaseContainer(Container):
    """Base container that includes the main content area."""
    
    def __init__(self, initial_content=None, **kwargs):
        super().__init__(**kwargs)
        self.initial_content = initial_content
    
    def compose(self) -> ComposeResult:
        # Main content area
        with Container(id="content") as self.content_container:
            if self.initial_content:
                yield self.initial_content
            else:
                yield Static()  # Placeholder for actual content


class PRManagerApp(App):
    CSS_PATH = "main.css"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),  # Add Ctrl+C as an alternative quit shortcut
    ]

    def compose(self) -> ComposeResult:
        print("DEBUG: PRManagerApp.compose")
        # MINIMAL TEST: Yield a simple widget to see if the app runs at all.
        yield Static("HELLO WORLD. If you see this, the app's core is working.", id="hello")
        # yield OrgSelector(self.on_org_selected)

    def on_org_selected(self, org):
        print(f"DEBUG: PRManagerApp.on_org_selected called with org={org}")
        # Remove OrgSelector and show RepoSelectionWidget (minimal logic for now)
        from textual.css.query import NoMatches
        try:
            org_selector = self.query_one("#org_selector", expect_type=OrgSelector)
            print("DEBUG: Removing OrgSelector from app")
            org_selector.remove()
        except NoMatches:
            print("DEBUG: OrgSelector not found in app")
        # Show repo selection widget (real logic)
        print(f"DEBUG: Mounting RepoSelectionWidget for org: {org}")
        self.mount(RepoSelectionWidget(owner=org, on_select=self.on_repo_selected))
        print("DEBUG: Mounted RepoSelectionWidget")

    
    def action_quit(self) -> None:
        """Handle the quit action."""
        self.exit()
        
    def get_content_container(self) -> Container:
        """Get the content container where main UI elements should be placed."""
        return self.query_one("#content")

    def __init__(self):
        super().__init__()
        self.selected_repo = None
        print("DEBUG: PRManagerApp.__init__")

    def load_config(self):
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                self.selected_repo = json.load(f).get("selected_repository", "")
        else:
            self.selected_repo = ""
        logging.info(f"Owner selected: {owner}")
        
        try:
            # Get the main container
            container = self.query_one("#main_container")
            if not container:
                error_msg = "Could not find main container"
                logging.error(error_msg)
                self.notify(error_msg, severity="error")
                return
            
            # Remove the org selector
            selector = container.query_one(OrgSelector)
            if selector:
                logging.info("Removing OrgSelector")
                selector.remove()
            
            # Create and mount the repo selector
            logging.info("Creating RepoSelectionWidget")
            repo_selector = RepoSelectionWidget(owner, self.on_repo_selected)
            
            # Mount the repo selector after a small delay to ensure the DOM is ready
            def mount_repo_selector():
                logging.info("Mounting RepoSelectionWidget")
                try:
                    container.mount(repo_selector)
                    logging.info("RepoSelectionWidget mounted successfully")
                except Exception as e:
                    error_msg = f"Failed to mount RepoSelectionWidget: {str(e)}"
                    logging.error(error_msg)
                    logging.error(traceback.format_exc())
                    self.notify(error_msg, severity="error")
            
            # Schedule the mount operation
            self.call_after_refresh(mount_repo_selector)
            
        except Exception as e:
            error_msg = f"Error in on_owner_selected: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            self.notify(error_msg, severity="error")

    def _show_error_in_ui(self, container, error_msg: str):
        """Helper function to display error in the UI"""
        logging.error(f"Showing error in UI: {error_msg}")
        if container is None:
            container = self.query_one("#main_container")
    
    def _process_repository(self, repo: str, container, loading_widget) -> None:
        """Process repository in a background thread"""
        import threading
        import traceback
        
        current_thread = threading.current_thread()
        thread_id = current_thread.ident
        
        def log(msg: str, level: str = 'info') -> None:
            """Helper function for consistent logging format"""
            log_msg = f"[Thread-{thread_id}] {msg}"
            if level == 'error':
                logging.error(log_msg)
            elif level == 'warning':
                logging.warning(log_msg)
            else:
                logging.info(log_msg)
        
        log(f"=== STARTING REPOSITORY PROCESSING FOR: {repo} ===")
        log(f"Thread name: {current_thread.name}")
        log(f"Is daemon: {current_thread.daemon}")
        log(f"Is alive: {current_thread.is_alive()}")
        
        def log_thread_status():
            log(f"Thread status - Alive: {current_thread.is_alive()}, Daemon: {current_thread.daemon}")
        
        # Log thread status periodically
        try:
            from threading import Timer
            status_timer = Timer(5.0, log_thread_status)
            status_timer.daemon = True
            status_timer.start()
            log("Started periodic status timer")
        except Exception as e:
            log(f"Failed to start status timer: {str(e)}", 'error')
            log(traceback.format_exc(), 'error')
        
        try:
            log("Setting up repository path...")
            clone_base = Path.home() / ".cache" / "gh_pr_manager"
            repo_path = clone_base / repo.replace("/", "_")
            log(f"Repository path: {repo_path}")
            log(f"Clone base exists: {clone_base.exists()}")
            
            # Clone or update the repository
            try:
                log(f"Checking if repository exists at: {repo_path}")
                repo_exists = repo_path.exists()
                log(f"Repository exists: {repo_exists}")
                if not repo_path.exists():
                    log("Repository does not exist, cloning...")
                    log(f"Ensuring parent directory exists: {repo_path.parent}")
                    try:
                        repo_path.parent.mkdir(parents=True, exist_ok=True)
                        log(f"Running: gh repo clone {repo} {repo_path}")
                        success, output = run_cmd(["gh", "repo", "clone", repo, str(repo_path)])
                        if not success:
                            error_msg = f"Failed to clone repository: {output}"
                            log(error_msg, 'error')
                            raise Exception(error_msg)
                        log("Repository cloned successfully")
                    except Exception as e:
                        log(f"Error during clone: {str(e)}", 'error')
                        log(traceback.format_exc(), 'error')
                        raise
                else:
                    log("Repository exists, pulling latest changes...")
                    log(f"Running: git -C {repo_path} pull")
                    try:
                        success, output = run_cmd(["git", "-C", str(repo_path), "pull"])
                        if not success:
                            log(f"Warning: Failed to pull repository: {output}", 'warning')
                        else:
                            log("Repository updated successfully")
                    except Exception as e:
                        log(f"Error during pull: {str(e)}", 'error')
                        log(traceback.format_exc(), 'error')
                        raise
            except Exception as e:
                logging.error(f"[Thread-{current_thread.ident}] Error in repository update: {str(e)}", exc_info=True)
                raise

            # Fetch all branches
            try:
                log("Fetching all branches...")
                log(f"Running: git -C {repo_path} fetch --prune")
                success, fetch_output = run_cmd(["git", "-C", str(repo_path), "fetch", "--prune"])
                if not success:
                    log(f"Warning: Failed to fetch branches: {fetch_output}", 'warning')
                else:
                    log("Successfully fetched branches")
                
                # Verify git repository
                log("Verifying git repository...")
                success, git_status = run_cmd(["git", "-C", str(repo_path), "status"])
                if not success:
                    log(f"Warning: Git status check failed: {git_status}", 'warning')
                else:
                    log("Git repository verified successfully")
                log("Getting branch list...")
                cmd = [
                    "git", "-C", str(repo_path), "for-each-ref",
                    "--format=%(refname:short)", "refs/remotes/origin/"
                ]
                log(f"Running: {' '.join(cmd)}")
                success, output = run_cmd(cmd)
                log(f"Command success: {success}, output length: {len(output) if output else 0}")
                if output:
                    log(f"First 200 chars of branch list: {output[:200]}")
                    
                if success:
                    if not output:
                        log("Warning: Branch list command succeeded but returned no output", 'warning')
                        # Try an alternative approach to get branches
                        log("Trying alternative branch listing command...")
                        alt_cmd = ["git", "-C", str(repo_path), "branch", "-r"]
                        log(f"Running: {' '.join(alt_cmd)}")
                        success, output = run_cmd(alt_cmd)
                        log(f"Alternative command success: {success}, output length: {len(output) if output else 0}")
                        if output:
                            log(f"First 200 chars of alternative branch list: {output[:200]}")
                
                if output:
                    branches = [b.replace('origin/', '') for b in output.splitlines() if b.strip()]
                    branches = [b for b in branches if not b.endswith('HEAD')]
                    log(f"Found {len(branches)} branches after filtering")
                    
                    if not branches:
                        log("No branches found after filtering. Raw output:", 'warning')
                        log(output, 'warning')
                else:
                    log("No branch data available", 'warning')
            except Exception as e:
                logging.error(f"[Thread-{current_thread.ident}] Error fetching branches: {str(e)}", exc_info=True)
                raise
            
            # Create and mount the branch selector
            try:
                log(f"=== CREATING BRANCH SELECTOR ===")
                log(f"Processing {len(branches)} branches...")
                
                if not branches:
                    log("Warning: No branches to display", 'warning')
                    self.call_after_refresh(
                        lambda: self._show_error_in_ui(container, "No branches found in repository")
                    )
                    return
                
                log(f"Sample branches for selector (first 5): {branches[:5]}")
                
                # Create the branch selector
                log("=== CREATING BRANCH SELECTOR INSTANCE ===")
                log(f"Number of branches to display: {len(branches)}")
                log(f"Sample branches (first 5): {branches[:5] if len(branches) > 5 else branches}")
                log(f"Repository path: {repo_path}")
                
                try:
                    log("Initializing BranchSelector...")
                    # Create a back callback function
                    def on_back():
                        log("Back button pressed, showing repo selector")
                        self.show_repo_selector()
                    
                    # Initialize BranchSelector with all required parameters
                    branch_selector = BranchSelector(
                        repo=repo,  # The repository name/path
                        branches=branches,  # List of branch names
                        on_back=on_back  # Callback for back button
                    )
                    
                    # Verify the branch selector was created correctly
                    if not hasattr(branch_selector, 'mount'):
                        raise Exception("BranchSelector is missing required 'mount' method")
                    
                    log("BranchSelector instance created successfully")
                    log(f"BranchSelector type: {type(branch_selector).__name__}")
                    log(f"BranchSelector ID: {getattr(branch_selector, 'id', 'N/A')}")
                    log(f"BranchSelector has mount method: {hasattr(branch_selector, 'mount')}")
                    log(f"BranchSelector parent: {getattr(branch_selector, 'parent', 'None')}")
                    
                    # Check if branch selector has the expected attributes
                    expected_attrs = ['branches', 'on_branch_selected', 'selected_branches']
                    for attr in expected_attrs:
                        log(f"BranchSelector has {attr}: {hasattr(branch_selector, attr)}")
                    
                except Exception as e:
                    error_msg = f"Failed to create BranchSelector: {str(e)}"
                    log(error_msg, 'error')
                    log(traceback.format_exc(), 'error')
                    raise Exception(f"BranchSelector creation failed: {str(e)}")
                
                # Schedule the branch selector to be mounted in the UI thread
                log("Scheduling branch selector mount in UI thread...")
                
                def safe_mount():
                    try:
                        log("[UI Thread] === STARTING BRANCH SELECTOR MOUNT ===")
                        log(f"[UI Thread] Container type: {type(container).__name__}")
                        
                        # Remove loading widget if it exists
                        if loading_widget and loading_widget in container.children:
                            try:
                                container.remove_child(loading_widget)
                                log("Removed loading widget")
                            except Exception as e:
                                log(f"Error removing loading widget: {str(e)}", 'warning')
                        
                        # Clear any existing content in the container
                        container.remove_children()
                        log("Cleared container children")
                        
                        # Mount the branch selector directly in the container
                        container.mount(branch_selector)
                        log("Branch selector mounted successfully")
                        
                        # Set focus to the branch selector if it has a focusable element
                        if hasattr(branch_selector, 'focus'):
                            branch_selector.focus()
                        
                    except Exception as e:
                        error_msg = f"Failed to mount branch selector: {str(e)}"
                        log(error_msg, 'error')
                        log(traceback.format_exc(), 'error')
                        self._show_error_in_ui(container, "Failed to load branch list. Check logs for details.")
                
                # Verify we have a valid container before scheduling the update
                if container and hasattr(container, 'mount'):
                    log("Scheduling branch selector mount...")
                    self.call_after_refresh(safe_mount)
                else:
                    log(f"Invalid container for mounting: {container}", 'error')
                    self._show_error_in_ui(container, "UI Error: Invalid container")
                    
                return  # Successfully scheduled mount
                
            except Exception as e:
                error_msg = f"Error in repository processing: {str(e)}"
                log(error_msg, 'error')
                log(traceback.format_exc(), 'error')
                self.call_after_refresh(
                    lambda: self._show_error_in_ui(container, f"Error: {str(e)}")
                )
        except Exception as outer_e:
            error_msg = f"Unexpected error in _process_repository: {str(outer_e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            self.call_after_refresh(
                lambda: self._show_error_in_ui(container, "An unexpected error occurred. Please check the logs.")
            )
                
    def mount_branch_selector(self, branch_selector, container, loading_widget):
        """Safely mount the branch selector and remove loading widget"""
        # Configure logging for this method
        logging.basicConfig(filename="branch_selector_debug.log", level=logging.DEBUG, filemode="a")
        
        def log(msg: str, level: str = 'info') -> None:
            """Helper function for consistent logging format"""
            log_msg = f"[UI Thread][mount_branch_selector] {msg}"
            if level == 'error':
                logging.error(log_msg)
            elif level == 'warning':
                logging.warning(log_msg)
            else:
                logging.info(log_msg)
            print(log_msg)  # Also print to console for immediate feedback
            
        log("=== STARTING BRANCH SELECTOR MOUNT ===")
        log(f"Container type: {type(container).__name__}")
        log(f"Container ID: {getattr(container, 'id', 'N/A')}")
        log(f"Container classes: {getattr(container, 'classes', 'N/A')}")
        if container and hasattr(container, 'children'):
            children_info = []
            for c in container.children:
                child_type = type(c).__name__
                child_id = getattr(c, 'id', 'N/A')
                children_info.append(f"{child_type}(id={child_id})")
            log(f"Container children: {children_info}" if children_info else "Container has no children")
        else:
            log("Container has no children or is invalid")
        log(f"Loading widget type: {type(loading_widget).__name__ if loading_widget else 'None'}")
        log(f"Loading widget ID: {getattr(loading_widget, 'id', 'N/A') if loading_widget else 'N/A'}")
        log(f"Branch selector type: {type(branch_selector).__name__}")
        log(f"Branch selector ID: {getattr(branch_selector, 'id', 'N/A')}")
        log(f"Branch selector has mount: {hasattr(branch_selector, 'mount')}")
        log(f"Branch selector branches: {getattr(branch_selector, 'branches', 'N/A')}" if hasattr(branch_selector, 'branches') else 'Branch selector has no branches attribute')
        
        try:
            # Remove loading widget if it exists
            if loading_widget is not None:
                log(f"\n=== PROCESSING LOADING WIDGET ===")
                log(f"Widget type: {type(loading_widget).__name__}")
                log(f"Widget ID: {getattr(loading_widget, 'id', 'N/A')}")
                log(f"Widget parent: {getattr(loading_widget, 'parent', 'None')}")
                
                try:
                    widget_removed = False
                    
                    # First check if widget is mounted in container
                    if container and hasattr(container, 'children'):
                        log(f"Container has {len(container.children)} children")
                        children_list = []
                        for c in container.children:
                            child_type = type(c).__name__
                            child_id = getattr(c, 'id', 'N/A')
                            children_list.append(f"{child_type}(id={child_id})")
                        log(f"Container children: {children_list}")
                        
                        if loading_widget in container.children:
                            log("Loading widget found in container, removing...")
                            try:
                                # Create a list of children to keep (excluding the loading widget)
                                children_to_keep = [c for c in container.children if c != loading_widget]
                                log(f"Will keep {len(children_to_keep)} children after removing loading widget")
                                
                                # Clear all children
                                container.remove_children()
                                log("All children removed from container")
                                
                                # Re-add non-loading widgets
                                if children_to_keep:
                                    log(f"Re-adding {len(children_to_keep)} non-loading widgets")
                                    for child in children_to_keep:
                                        try:
                                            container.mount(child)
                                            log(f"Re-added child: {type(child).__name__}(id={getattr(child, 'id', 'N/A')})")
                                        except Exception as mount_error:
                                            log(f"Error re-adding child: {str(mount_error)}", 'error')
                                
                                widget_removed = True
                                log("Loading widget removed from container")
                                
                            except Exception as remove_error:
                                log(f"Error removing loading widget: {str(remove_error)}", 'error')
                                log(traceback.format_exc(), 'error')
                    
                    # If not removed from container, try removing from parent
                    if not widget_removed and hasattr(loading_widget, 'parent') and loading_widget.parent is not None:
                        parent = loading_widget.parent
                        log(f"Loading widget has parent: {type(parent).__name__}")
                        if hasattr(parent, 'children'):
                            try:
                                # Remove the widget by clearing children and re-adding any non-loading widgets
                                children = list(parent.children)
                                parent.remove_children()
                                for child in children:
                                    if child != loading_widget:
                                        parent.mount(child)
                                log("Loading widget removed from parent")
                                widget_removed = True
                            except Exception as remove_error:
                                log(f"Error removing from parent: {str(remove_error)}", 'error')
                    
                    if not widget_removed:
                        log("Loading widget not found in container or parent", 'warning')
                        # As a last resort, try to clear all children
                        try:
                            container.remove_children()
                            log("Cleared all children from container as fallback")
                            widget_removed = True
                        except Exception as e:
                            log(f"Failed to clear container: {str(e)}", 'error')
                except Exception as remove_error:
                    log(f"Error removing loading widget: {str(remove_error)}", 'error')
                    log(traceback.format_exc(), 'error')
            else:
                log("No loading widget to process")
            
            # Mount the branch selector
            log("Preparing to mount branch selector...")
            log(f"Branch selector children: {[type(c).__name__ for c in branch_selector.children] if hasattr(branch_selector, 'children') else 'N/A'}")
            
            # Check if branch selector is already mounted
            if hasattr(branch_selector, 'parent') and branch_selector.parent is not None:
                log(f"Branch selector already has parent: {type(branch_selector.parent).__name__}")
                if hasattr(branch_selector.parent, 'remove_child'):
                    log("Removing branch selector from current parent...")
                    branch_selector.parent.remove_child(branch_selector)
            
            # Clear container before mounting new content
            try:
                log("Clearing container children...")
                container.remove_children()
                log(f"Container cleared. New children: {[type(c).__name__ for c in container.children]}")
            except Exception as clear_error:
                log(f"Warning: Failed to clear container: {str(clear_error)}", 'warning')
            
            # Mount the branch selector
            log("Mounting branch selector...")
            try:
                # Ensure container is mounted and has a screen
                if not hasattr(container, 'mount'):
                    raise Exception("Container does not have mount method")
                
                # Clear container first
                container.remove_children()
                
                # Mount the branch selector
                container.mount(branch_selector)
                log(f"Branch selector mounted successfully. Container children: {[type(c).__name__ for c in container.children]}")
                
                # Verify the branch selector is in the container
                if branch_selector not in container.children:
                    error_msg = "Failed to mount branch selector: not found in container after mount"
                    log(error_msg, 'error')
                    raise Exception(error_msg)
                
                # Force a layout refresh
                log("Refreshing layout...")
                try:
                    self.refresh(layout=True)
                    log("Layout refresh completed")
                except Exception as refresh_error:
                    log(f"Warning: Error during layout refresh: {str(refresh_error)}", 'warning')
                    log(traceback.format_exc(), 'warning')
                
                # Try to focus the list view inside the branch selector
                try:
                    list_view = branch_selector.query_one("#branch_list")
                    if list_view and hasattr(list_view, 'focus'):
                        list_view.focus()
                        log("Focused branch list view")
                    else:
                        # If no list view, try to focus the branch selector itself
                        branch_selector.focus()
                        log("Focused branch selector")
                except Exception as focus_error:
                    log(f"Warning: Could not focus list view or branch selector: {str(focus_error)}", 'warning')
                
            except Exception as mount_error:
                error_msg = f"Failed to mount branch selector: {str(mount_error)}"
                log(error_msg, 'error')
                log(traceback.format_exc(), 'error')
                raise
            
            log("Branch selector mount completed successfully")
            return True
            
        except Exception as e:
            error_msg = f"Critical error in mount_branch_selector: {str(e)}"
            log(error_msg, 'error')
            log(traceback.format_exc(), 'error')
            
            # Try to show error in UI if possible
            try:
                self._show_error_in_ui(container, "Failed to load branch list. Please check logs.")
            except Exception as ui_error:
                log(f"Failed to show error in UI: {str(ui_error)}", 'error')
            
            # Re-raise to allow caller to handle the error
            raise
            
        finally:
            log("=== BRANCH SELECTOR MOUNT PROCESS COMPLETE ===")

    def on_repo_selected(self, repo: str) -> None:
        """Handle repository selection"""
        def log(msg: str, level: str = 'info') -> None:
            """Helper function for consistent logging format"""
            log_msg = f"[UI Thread] {msg}"
            if level == 'error':
                logging.error(log_msg)
            elif level == 'warning':
                logging.warning(log_msg)
            else:
                logging.info(log_msg)
            print(log_msg)  # Also print to console for immediate feedback
        
        # Configure logging
        logging.basicConfig(
            filename="repo_debug.log", 
            level=logging.DEBUG, 
            filemode="a",
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        log(f"=== REPOSITORY SELECTED: {repo} ===")
        log(f"Current thread: {threading.current_thread().name}")
        log(f"Is main thread: {threading.current_thread() is threading.main_thread()}")
        
        try:
            # Get the container where we'll show the loading widget and branch selector
            container = self.query_one("#main_container")
            if not container:
                error_msg = "Error: Could not find main container"
                log(error_msg, 'error')
                self._show_error_in_ui(None, error_msg)
                return
                
            log(f"Found container: {container}")
            
            # Create and show loading widget
            loading = Label("Fetching repository data...", id="loading-widget")
            log("Created loading widget")
            
            # Clear the container and show loading
            try:
                # Clear existing children
                container.remove_children()
                container.mount(loading)
                log("Mounted loading widget")
                
                # Force a UI refresh to show the loading widget
                self.refresh()
                log("Forced UI refresh after mounting loading widget")
                
            except Exception as e:
                error_msg = f"Error updating UI: {str(e)}"
                log(error_msg, 'error')
                log(traceback.format_exc(), 'error')
                self._show_error_in_ui(container, "Failed to initialize UI")
                return
                
            # Start repository processing in a background thread
            log("Starting repository processing in background thread...")
            
            try:
                thread = threading.Thread(
                    target=self._process_repository,
                    args=(repo, container, loading),
                    daemon=True,
                    name=f"RepoProcessor-{repo}"
                )
                thread.start()
                log(f"Started background thread: {thread.name}")
                
                # Set a timer to check if the thread is still alive after a delay
                def check_thread_status():
                    if thread.is_alive():
                        log("Background thread is still running after delay", 'warning')
                        # If thread is stuck, show an error to the user
                        self.call_after_refresh(
                            lambda: self._show_error_in_ui(
                                container,
                                "Repository processing is taking longer than expected. Please check your connection and try again."
                            )
                        )
                    else:
                        log("Background thread completed successfully")
                
                # Check after 15 seconds
                timer = threading.Timer(15.0, check_thread_status)
                timer.daemon = True
                timer.start()
                log("Started thread status check timer")
                
            except Exception as e:
                error_msg = f"Failed to start repository processing: {str(e)}"
                log(error_msg, 'error')
                log(traceback.format_exc(), 'error')
                self._show_error_in_ui(container, "Failed to start repository processing")
            
            # Update config with the selected repository
            try:
                log(f"Updating config file at {CONFIG_PATH}")
                with open(CONFIG_PATH, "w") as f:
                    json.dump({"selected_repository": repo}, f, indent=2)
                log("Successfully updated config file")
            except Exception as e:
                error_msg = f"Error updating config: {str(e)}"
                log(error_msg, 'error')
                log(traceback.format_exc(), 'error')
                
        except Exception as e:
            error_msg = f"Error in on_repo_selected: {str(e)}"
            log(error_msg, 'error')
            log(traceback.format_exc(), 'error')
            self._show_error_in_ui(None, f"Error: {error_msg}")
            # Use call_after_refresh to ensure UI updates happen in the main thread
            self.call_after_refresh(lambda: self._show_error_in_ui(None, error_msg))
            return
            
            log("Locating main container...")
            container = self.query_one("#main_container")
            if not container:
                error_msg = "Could not find #main_container in UI"
                log(error_msg, 'error')
                return
            
            log("Clearing existing widgets...")
            try:
                container.remove_children()
                log("Container cleared successfully")
            except Exception as e:
                log(f"Warning: Failed to clear container: {str(e)}", 'warning')
            
            # Show loading message
            log("Mounting loading widget...")
            loading = Static("Loading repository data...", id="loading-widget")
            try:
                container.mount(loading)
                log("Loading widget mounted successfully")
                self.call_after_refresh(lambda: log("Loading message confirmed visible in UI"))
            except Exception as e:
                log(f"Failed to mount loading widget: {str(e)}", 'error')
                log(traceback.format_exc(), 'error')
            
            # Start the background task
            log("Preparing to start background thread...")
            try:
                import threading
                log("Creating background thread...")
                thread = threading.Thread(
                    target=self._process_repository,
                    args=(repo, container, loading),
                    daemon=True,
                    name=f"RepoProcessor-{repo}"
                )
                
                log(f"Starting background thread: {thread.name}")
                thread.start()
                log(f"Background thread started (alive: {thread.is_alive()})")
                
                # Add a timeout check for the thread
                def check_thread():
                    if thread.is_alive():
                        log("Background thread is still running - possible hang detected", 'warning')
                        self.call_after_refresh(
                            lambda: self._show_error_in_ui(
                                container, 
                                "Repository processing is taking too long. Please try again."
                            )
                        )
                    else:
                        log("Background thread completed successfully")
                
                # Schedule a check after 30 seconds
                from threading import Timer
                timer = Timer(30.0, check_thread)
                timer.daemon = True
                timer.start()
                log(f"Thread timeout check scheduled in 30 seconds (timer alive: {timer.is_alive()})")
                
            except Exception as e:
                error_msg = f"Failed to start repository processing: {str(e)}"
                log(error_msg, 'error')
                log(traceback.format_exc(), 'error')
                self.call_after_refresh(lambda: self._show_error_in_ui(container, error_msg))
                
        except Exception as e:
            error_msg = f"Unexpected error in repository selection: {str(e)}"
            log(error_msg, 'error')
            log(traceback.format_exc(), 'error')
            try:
                self.call_after_refresh(lambda: self._show_error_in_ui(container, error_msg))
            except Exception as ui_error:
                log(f"Failed to show error in UI: {str(ui_error)}", 'error')
        
        log("=== REPOSITORY SELECTION PROCESS COMPLETE ===")

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
    print("DEBUG: main.py starting up")
    PRManagerApp().run()
    print("DEBUG: PRManagerApp has exited")
