# Contributor Guide for GitHub PR Manager

## Overview
- **Source code:** All main application code is in `src/gh_pr_manager/`.
- **Tests:** All tests are in `tests/` and should use `pytest`.
- **Configuration:** Project-wide settings and repo lists are in `config.json`.
- **Documentation:** See `README.md` for setup and usage. This `AGENTS.md` provides agent and contributor guidelines.

## Dev Environment Tips
- Use Python 3.11+ (managed via `pyenv`), with a `uv`-managed virtual environment in `.venv`.
- Install dependencies with:
  ```bash
  uv pip install -r requirements.txt
  uv pip install -r requirements-dev.txt
  ```
- Run the TUI app from the project root with:
  ```bash
  python -m gh_pr_manager
  ```
- The TUI uses the [Textual](https://github.com/Textualize/textual) library.

## Contribution and Style Guidelines
- Follow PEP8 for code style.
- Organize new modules under `src/gh_pr_manager/`.
- Keep business logic separated from UI code where possible.
- Use descriptive commit messages and PR titles.

## Testing Instructions
- All tests must pass before merging. Run tests with:
  ```bash
  pytest
  ```
- Add or update tests for any new features or bug fixes.
- Use `pytest-asyncio` for async tests (e.g., for Textual UI logic).
- Integration/UI tests should use the official Textual `Pilot` and `run_test()` utilities.

## PR Instructions
- Title format: `[gh-pr-manager] <Your descriptive title>`
- Include a summary of changes and testing steps in the PR body.
- Reference related issues or user stories if applicable.

## Validation Checklist
- [ ] All tests pass (`pytest`)
- [ ] Manual TUI check for new/changed features
- [ ] Code follows style and structure guidelines

## Migration/Refactor Notes
- The project uses a modern `src/` layout.
- If moving files or changing imports, ensure `pytest.ini` and all import paths are updated.

## Agent/Automation Notes
- When exploring or editing, prefer `src/gh_pr_manager/` for main code and `tests/` for tests.
- Always update or create documentation (`README.md`, `AGENTS.md`) when introducing new major features or workflows.
- Use this file for any future organization-wide or agent-specific configuration.
