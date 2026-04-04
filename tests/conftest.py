"""Shared test fixtures — all tests run WITHOUT Schrödinger installed."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_config_file(tmp_path: Path) -> Path:
    """Write a minimal YAML config and return its path."""
    config = tmp_path / "config.yaml"
    config.write_text("""\
job_name: test_fep
gpu_id: 0
protein_file: protein.pdb
ligand_file: ligands.smi
output_dir: output

server:
  host: user@localhost
  schrodinger: /opt/schrodinger
  workdir: /tmp/workdir
  scratch: /tmp/scratch

prep:
  ph: 7.0
  force_field: OPLS4

docking:
  precision: SP
  poses_per_lig: 1

fep:
  sim_time: 100
  lambda_windows: 6
  force_field: OPLS4

abfe:
  fep_sim_time: 1000
  md_sim_time: 200
""")
    return config


@pytest.fixture
def sample_smiles_file(tmp_path: Path) -> Path:
    """Write a sample SMILES file and return its path."""
    smi = tmp_path / "ligands.smi"
    smi.write_text("""\
# Test ligands
c1ccccc1\tbenzene
Cc1ccccc1\ttoluene
CCc1ccccc1\tethylbenzene
""")
    return smi


@pytest.fixture
def sample_csv_file(tmp_path: Path) -> Path:
    """Write a sample FEP+ summary CSV and return its path."""
    csv_file = tmp_path / "summary.csv"
    csv_file.write_text("""\
Title,FEP+ dG (kcal/mol),FEP+ ddG (kcal/mol),Uncertainty,Exp. dG (kcal/mol)
benzene,-5.10,0.00,0.15,-5.19
toluene,-5.60,-0.50,0.20,-5.49
ethylbenzene,-4.90,0.20,0.25,-5.07
p-xylene,-6.10,-1.00,0.18,-5.96
chlorobenzene,-5.30,-0.20,0.22,-5.42
phenol,-4.50,0.60,0.30,-4.73
""")
    return csv_file
