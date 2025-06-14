# GitHub PR Manager

A text-based user interface (TUI) Python app for managing GitHub branches and pull requests using the `gh` CLI.

## Features
- Select a repository from a pre-configured list
- List, delete, or select branches
- Create, merge, and delete branches via PR in one step
- Interactive branch actions widget for deleting or merging via PR
- Edit the list of managed repositories within the TUI

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
Use the **Edit Repositories** view or modify `config.json` manually.
