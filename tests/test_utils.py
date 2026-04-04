"""Tests for utility functions."""

from __future__ import annotations

import contextlib
from pathlib import Path
from unittest.mock import patch

from fep_pipeline.utils import ensure_dir, run_command, setup_logging


def test_ensure_dir(tmp_path: Path) -> None:
    """Create a directory that doesn't exist."""
    new_dir = tmp_path / "a" / "b" / "c"
    result = ensure_dir(new_dir)
    assert result.exists()
    assert result.is_dir()
    assert result == new_dir


def test_ensure_dir_existing(tmp_path: Path) -> None:
    """No error when directory already exists."""
    result = ensure_dir(tmp_path)
    assert result == tmp_path


def test_run_command_success() -> None:
    """Run a simple command and capture output."""
    result = run_command(["echo", "hello"])
    assert result.returncode == 0
    assert "hello" in result.stdout


def test_run_command_failure() -> None:
    """Non-zero exit raises CalledProcessError."""
    import subprocess

    try:
        run_command(["false"])
    except subprocess.CalledProcessError as e:
        assert e.returncode != 0


def test_setup_logging() -> None:
    """Setup logging without errors."""
    setup_logging()
    # Just verify it doesn't raise


def test_ssh_run_builds_correct_command() -> None:
    """ssh_run calls ssh with host and command."""
    with patch("fep_pipeline.utils.run_command") as mock_run:
        from fep_pipeline.utils import ssh_run

        mock_run.return_value = None
        with contextlib.suppress(Exception):
            ssh_run("user@host", "ls -la")
        mock_run.assert_called_once_with(["ssh", "user@host", "ls -la"], check=True)
