import subprocess
from pathlib import Path
from typing import List, Tuple


def run_cmd(cmd: List[str], cwd: str | Path | None = None) -> tuple[bool, str]:
    """Run a subprocess command and return success status and output."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False, f"Command not found: {cmd[0]}"
    except Exception as exc:
        return False, str(exc)

    if result.returncode != 0:
        output = result.stderr.strip() or result.stdout.strip()
        return False, output
    return True, result.stdout


def filter_valid_repos(repos: List[str]) -> Tuple[List[str], List[str]]:
    """Separate valid and invalid repository paths."""
    valid: List[str] = []
    invalid: List[str] = []
    for repo in repos:
        if Path(repo).is_dir():
            valid.append(repo)
        else:
            invalid.append(repo)
    return valid, invalid
