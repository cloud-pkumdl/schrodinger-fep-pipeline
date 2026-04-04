"""Helpers — logging setup, structure I/O wrappers, remote execution."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("fep_pipeline")


def setup_logging(level: int = logging.INFO) -> None:
    """Configure package-level logging with a simple console handler.

    Args:
        level: Logging level (default INFO).
    """
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(name)s] %(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(level)


def run_command(
    cmd: list[str],
    *,
    cwd: str | Path | None = None,
    check: bool = True,
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a local shell command with logging.

    Args:
        cmd: Command as list of strings.
        cwd: Working directory.
        check: Raise on non-zero exit code.
        capture: Capture stdout/stderr.

    Returns:
        CompletedProcess result.
    """
    logger.debug("Running: %s", " ".join(cmd))
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        capture_output=capture,
        text=True,
    )


def ssh_run(host: str, command: str, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Execute a command on a remote host via SSH.

    Args:
        host: SSH host string (e.g. user@host).
        command: Shell command to execute remotely.
        check: Raise on non-zero exit code.

    Returns:
        CompletedProcess result.
    """
    return run_command(["ssh", host, command], check=check)


def scp_upload(host: str, local_path: str | Path, remote_path: str) -> None:
    """Upload a file to a remote host via SCP.

    Args:
        host: SSH host string.
        local_path: Local file path.
        remote_path: Remote destination path.
    """
    run_command(["scp", str(local_path), f"{host}:{remote_path}"])


def scp_download(host: str, remote_path: str, local_path: str | Path) -> None:
    """Download a file from a remote host via SCP.

    Args:
        host: SSH host string.
        remote_path: Remote file path.
        local_path: Local destination path.
    """
    run_command(["scp", f"{host}:{remote_path}", str(local_path)])


def ensure_dir(path: str | Path) -> Path:
    """Create a directory if it doesn't exist, return the Path.

    Args:
        path: Directory path to ensure.

    Returns:
        The directory Path.
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def schrodinger_run(
    schrodinger_path: str,
    host: str,
    command: str,
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a command under $SCHRODINGER/run on a remote host.

    Args:
        schrodinger_path: Path to Schrödinger installation.
        host: SSH host string.
        command: Command to run under $SCHRODINGER/run.
        check: Raise on non-zero exit code.

    Returns:
        CompletedProcess result.
    """
    full_cmd = f"{schrodinger_path}/run {command}"
    return ssh_run(host, full_cmd, check=check)
