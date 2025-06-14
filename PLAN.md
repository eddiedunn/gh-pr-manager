# GitHub PR Manager: Internal Plan (June 2025)

## Overview
This document tracks the current technical direction and design for the repository selection refactor. It is intended to preserve context for future contributors.

---

## Background
- The app previously managed a list of local repository paths in `config.json`.
- The new requirement is to select a repository by connecting to GitHub, choosing an organization/account, and then picking a repository from a searchable list.
- Only one repository is selected per launch/session. The GitHub authentication is reused as long as the token is available.
- All actions (branch management, PRs) are performed via the GitHub API and `gh` CLI.

---

## Functional Flow
1. **GitHub Authentication**
    - On first launch (or if token is missing/invalid), prompt user to authenticate (OAuth or Personal Access Token).
    - Store token securely (local file, keyring, or env var).
2. **Organization/Account Selection**
    - Fetch organizations and user account from GitHub API.
    - User selects which org/account to browse.
3. **Repository Selection**
    - Fetch all repositories for the selected org/account (paginated if needed).
    - User searches and selects a single repository.
    - The selected repo is stored in `config.json` as `org/repo`.
4. **Branch & PR Management**
    - App operates on the selected repository for the session.
    - Standard branch and PR actions are available via the TUI.

---

## UI Components
- **GitHubAuthWidget**: Handles authentication prompt and token validation/storage.
- **OrgSelectorWidget**: Lets user pick an organization or their own account.
- **RepoSelectorWidget**: Searchable, single-select list of repositories in the chosen org/account.
- **MainAppFlow**: Orchestrates the above steps and transitions to branch/PR management.

---

## Backend/API Logic
- Use stored token for all GitHub API calls:
    - `GET /user/orgs` to fetch orgs
    - `GET /user` for user account
    - `GET /orgs/{org}/repos` or `GET /user/repos` for repos
- Store selected repo as canonical GitHub name (`org/repo`) in config.
- On launch, pre-select last used repo if token is valid.
- Use `gh` CLI or API for branch management.

---

## Error Handling & UX
- Show clear errors for invalid tokens or API failures.
- Allow re-authentication if needed.
- Provide loading indicators during network calls.

---

## Migration Notes
- Old config with local repo paths is no longer supported.
- Users must re-select their repo using the new GitHub-based flow.

---

## Outstanding Tasks
- [ ] Implement GitHubAuthWidget and token storage
- [ ] Implement OrgSelectorWidget
- [ ] Implement RepoSelectorWidget (single-select)
- [ ] Update config handling for single `org/repo`
- [ ] Update README and migration docs (done)
- [ ] Test end-to-end flow

---

## Contact
For questions or handoff, see the most recent committers in the repo or reach out via the team Slack channel.

---

## Technical Details

### GitHub API Usage

* We will use the GitHub API to fetch organizations, user account, and repositories.
* We will use the `gh` CLI to perform branch management actions.

### Token Storage

* We will store the GitHub token securely using a local file, keyring, or environment variable.
* We will validate the token on each launch and prompt the user to re-authenticate if it is invalid.

### UI Component Details

* **GitHubAuthWidget**: This widget will handle the authentication prompt and token validation/storage. It will also provide a way for the user to re-authenticate if needed.
* **OrgSelectorWidget**: This widget will let the user pick an organization or their own account. It will fetch the list of organizations and user account from the GitHub API.
* **RepoSelectorWidget**: This widget will provide a searchable, single-select list of repositories in the chosen org/account. It will fetch the list of repositories from the GitHub API.
* **MainAppFlow**: This component will orchestrate the above steps and transition to branch/PR management.

### Branch & PR Management

* We will use the `gh` CLI to perform branch management actions.
* We will provide standard branch and PR actions via the TUI.

### Error Handling & UX

* We will show clear errors for invalid tokens or API failures.
* We will allow re-authentication if needed.
* We will provide loading indicators during network calls.

### Migration Details

* We will no longer support the old config with local repo paths.
* Users must re-select their repo using the new GitHub-based flow.

### Documentation

* We will update the README and migration docs to reflect the new changes.
* We will provide clear instructions on how to use the new GitHub-based flow.

---

## Detailed Design

### GitHubAuthWidget

* The GitHubAuthWidget will be responsible for handling the authentication prompt and token validation/storage.
* It will provide a way for the user to re-authenticate if needed.
* It will store the token securely using a local file, keyring, or environment variable.

### OrgSelectorWidget

* The OrgSelectorWidget will be responsible for letting the user pick an organization or their own account.
* It will fetch the list of organizations and user account from the GitHub API.
* It will provide a list of organizations and user account for the user to select from.

### RepoSelectorWidget

* The RepoSelectorWidget will be responsible for providing a searchable, single-select list of repositories in the chosen org/account.
* It will fetch the list of repositories from the GitHub API.
* It will provide a list of repositories for the user to select from.

### MainAppFlow

* The MainAppFlow will be responsible for orchestrating the above steps and transitioning to branch/PR management.
* It will handle the logic for selecting a repository and storing it in the config.
* It will handle the logic for performing branch management actions.

### Branch & PR Management

* We will use the `gh` CLI to perform branch management actions.
* We will provide standard branch and PR actions via the TUI.

### Error Handling & UX

* We will show clear errors for invalid tokens or API failures.
* We will allow re-authentication if needed.
* We will provide loading indicators during network calls.

### Migration Details

* We will no longer support the old config with local repo paths.
* Users must re-select their repo using the new GitHub-based flow.

### Documentation

* We will update the README and migration docs to reflect the new changes.
* We will provide clear instructions on how to use the new GitHub-based flow.
