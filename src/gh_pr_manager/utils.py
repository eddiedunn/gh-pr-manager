import subprocess
from pathlib import Path
from typing import List, Union, Tuple


def run_cmd(cmd: List[str], cwd: Union[str, Path, None] = None) -> Tuple[bool, str]:
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



