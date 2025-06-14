# GitHub PR Manager

A text-based user interface (TUI) Python app for managing GitHub branches and pull requests using the `gh` CLI.

## Features
- Store the last selected repository for quick access
- Choose a repository from your GitHub organizations or account
- List, delete, or select branches
- Create, merge, and delete branches via PR in one step
- Interactive branch actions widget for deleting or merging via PR

## Requirements
- Python 3.8+
- [GitHub CLI (`gh`)](https://cli.github.com/)
- [textual](https://github.com/Textualize/textual)

## Setup
```bash
pip install -r requirements.txt
```

Authenticate the GitHub CLI before running the app:
```bash
gh auth login
```

## Run
```bash
python main.py
```

## Repository and Branch Workflow (Updated)

1. Launch the app and connect your GitHub account with `gh auth login`.
2. Select a GitHub organization or your personal account to browse repositories.
3. Search and select a single repository from the list. The app clones the repo
   to a temporary cache directory (or updates the existing clone).
4. The TUI displays the branches for the selected repository.
5. Use **Delete Branch** to remove the selected branch.
6. Use **PR/Merge/Delete** to create a pull request, merge it via the GitHub CLI, and delete the branch in one step.
7. From the repository selection screen you can change your selected GitHub repository at any time.

## Configuration
The selected repository is stored in `config.json` at the project root as the canonical GitHub repository name (e.g., `org/repo`).

- On first launch, you will be prompted to authenticate using `gh auth login`.
- You can update your selected repository at any time via the TUI.
- The app no longer tracks local repository paths; all actions are performed via the GitHub API and the `gh` CLI.

### Migration Note
If you previously used local paths in your config, you will need to re-select your repository using the new GitHub-based flow. The old format is no longer supported.
