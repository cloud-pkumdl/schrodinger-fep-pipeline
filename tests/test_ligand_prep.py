"""Tests for ligand preparation module."""

from __future__ import annotations

from pathlib import Path

import pytest

from fep_pipeline.ligand_prep import build_ligprep_cmd, read_smiles_file


def test_read_smiles_file(sample_smiles_file: Path) -> None:
    """Parse a tab-delimited SMILES file."""
    compounds = read_smiles_file(sample_smiles_file)
    assert len(compounds) == 3
    assert compounds[0] == ("c1ccccc1", "benzene")
    assert compounds[1] == ("Cc1ccccc1", "toluene")
    assert compounds[2] == ("CCc1ccccc1", "ethylbenzene")


def test_read_smiles_file_missing() -> None:
    """Raise FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        read_smiles_file("/nonexistent/ligands.smi")


def test_read_smiles_skips_comments(tmp_path: Path) -> None:
    """Comment lines and blanks are skipped."""
    smi = tmp_path / "test.smi"
    smi.write_text("# header\n\nc1ccccc1\tbenzene\n# another comment\nCc1ccccc1\ttoluene\n")
    compounds = read_smiles_file(smi)
    assert len(compounds) == 2


def test_build_ligprep_cmd() -> None:
    """Build a LigPrep command with expected flags."""
    cmd = build_ligprep_cmd(
        "/opt/schrodinger",
        "input.smi",
        "output.maegz",
        job_name="test_lp",
        force_field="OPLS4",
        ph=7.0,
    )
    assert cmd[0] == "/opt/schrodinger/ligprep"
    assert "-JOBNAME" in cmd
    assert "test_lp" in cmd
    assert "-epik" in cmd
    assert "-ifile" in cmd
    assert "input.smi" in cmd
    assert "-ofile" in cmd
    assert "output.maegz" in cmd


def test_build_ligprep_cmd_opls5() -> None:
    """OPLS5 force field uses bff 16."""
    cmd = build_ligprep_cmd(
        "/opt/schrodinger",
        "input.smi",
        "output.maegz",
        force_field="OPLS5",
    )
    idx = cmd.index("-bff")
    assert cmd[idx + 1] == "16"
