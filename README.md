# GitHub PR Manager

A text-based user interface (TUI) Python app for managing GitHub branches and pull requests using the `gh` CLI.

## Features
- Select a repository from a pre-configured list
- List, delete, or select branches
- Create, merge, and delete branches via PR in one step
- Update the list of managed repositories

## Requirements
- Python 3.8+
- [GitHub CLI (`gh`)](https://cli.github.com/)
- [textual](https://github.com/Textualize/textual)

## Setup
```bash
pip install -r requirements.txt
```

## Run
```bash
python main.py
```

## Configuration
Edit `config.json` to add/remove repositories.
