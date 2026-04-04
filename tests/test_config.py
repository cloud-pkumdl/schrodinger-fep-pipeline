"""Tests for pipeline configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from fep_pipeline.config import PipelineConfig, load_config


def test_load_config_basic(tmp_config_file: Path) -> None:
    """Load a valid config and check fields."""
    cfg = load_config(tmp_config_file)
    assert isinstance(cfg, PipelineConfig)
    assert cfg.job_name == "test_fep"
    assert cfg.gpu_id == 0
    assert cfg.protein_file == "protein.pdb"
    assert cfg.ligand_file == "ligands.smi"


def test_load_config_server(tmp_config_file: Path) -> None:
    """Check nested server config."""
    cfg = load_config(tmp_config_file)
    assert cfg.server.host == "user@localhost"
    assert cfg.server.schrodinger == "/opt/schrodinger"


def test_load_config_fep(tmp_config_file: Path) -> None:
    """Check FEP settings."""
    cfg = load_config(tmp_config_file)
    assert cfg.fep.sim_time == 100
    assert cfg.fep.lambda_windows == 6
    assert cfg.fep.force_field == "OPLS4"


def test_load_config_abfe(tmp_config_file: Path) -> None:
    """Check ABFE settings."""
    cfg = load_config(tmp_config_file)
    assert cfg.abfe.fep_sim_time == 1000
    assert cfg.abfe.md_sim_time == 200


def test_load_config_defaults(tmp_path: Path) -> None:
    """Minimal config uses defaults for missing fields."""
    cfg_file = tmp_path / "minimal.yaml"
    cfg_file.write_text("job_name: minimal\n")
    cfg = load_config(cfg_file)
    assert cfg.job_name == "minimal"
    assert cfg.fep.sim_time == 5000  # default
    assert cfg.fep.lambda_windows == 12  # default


def test_load_config_missing_file() -> None:
    """Raise FileNotFoundError for missing config."""
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/config.yaml")


def test_load_config_empty(tmp_path: Path) -> None:
    """Empty YAML file returns defaults."""
    cfg_file = tmp_path / "empty.yaml"
    cfg_file.write_text("")
    cfg = load_config(cfg_file)
    assert cfg.job_name == "fep_job"  # default
