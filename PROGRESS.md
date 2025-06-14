# Project Progress Tracker: GitHub PR Manager

This document tracks the tasks, milestones, and ongoing progress for the development of the GitHub PR Manager TUI application.

## Milestones & Task List

### Core Functionality
- [x] Project structure: modern `src/` layout, test infra, and config files
- [x] Pytest-based test infrastructure with Textual integration
- [x] AGENTS.md and documentation setup
- [x] Repository selection UI from pre-configured list
- [x] Branch listing UI after repo selection
- [x] Branch actions: delete, PR+merge+delete flow
- [ ] Repo list editing flow (add/remove repos)
- [ ] Error handling and user feedback for all flows
  - [ ] Handle missing/invalid repositories
  - [ ] Handle gh CLI errors
  - [ ] Handle network and authentication errors
  - [ ] Provide clear user feedback for all actions
- [ ] Testing
  - [ ] Unit tests for config and logic
  - [ ] Integration tests for TUI flows
  - [ ] Mock gh CLI for tests
  - [ ] Test error scenarios and edge cases
- [ ] Documentation updates
  - [ ] Update README.md for new features
  - [ ] Update AGENTS.md for process or structure changes
  - [ ] Update PROGRESS.md as tasks are completed

### Advanced/Optional
- [ ] Support for multiple remotes
- [ ] Customizable PR templates
- [ ] User settings/config UI
- [ ] Integration with CI status
- [ ] Keyboard shortcuts customization

## Progress Log

- **2025-06-14:** Project initialized, test infra working, AGENTS.md added, planning and requirements clarified.

---

## How to Update
- Mark tasks as `[x]` when complete.
- Add new tasks/features as needed.
- Use the Progress Log section to note major milestones or decisions.
