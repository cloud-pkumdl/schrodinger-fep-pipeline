"""Pipeline configuration — loads YAML config and provides typed defaults."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ServerConfig:
    """Remote compute server settings."""

    host: str = "cloud@100.71.111.116"
    schrodinger: str = "/opt/schrodinger2025-4"
    workdir: str = "/data2/cloud/schrodinger-skills"
    scratch: str = "/scratch/cloud-skills-test"


@dataclass
class PrepConfig:
    """Protein and ligand preparation settings."""

    ph: float = 7.0
    fill_loops: bool = True
    fill_side_chains: bool = True
    minimize_hydrogens: bool = True
    force_field: str = "OPLS4"
    water_dist: float = 5.0


@dataclass
class DockingConfig:
    """Glide docking settings."""

    precision: str = "SP"
    poses_per_lig: int = 1
    grid_center: list[float] = field(default_factory=list)
    grid_inner_box: float = 10.0
    grid_outer_box: float = 25.0


@dataclass
class FEPConfig:
    """FEP+ simulation settings."""

    sim_time: int = 5000
    lambda_windows: int = 12
    force_field: str = "OPLS4"
    ensemble: str = "NPT"
    temperature: float = 300.0


@dataclass
class ABFEConfig:
    """Absolute binding free energy settings."""

    fep_sim_time: int = 5000
    md_sim_time: int = 500
    force_field: str = "OPLS4"


@dataclass
class PipelineConfig:
    """Top-level pipeline configuration."""

    job_name: str = "fep_job"
    gpu_id: int = 1
    multi_gpus: str = ""
    protein_file: str = ""
    ligand_file: str = ""
    output_dir: str = "output"

    server: ServerConfig = field(default_factory=ServerConfig)
    prep: PrepConfig = field(default_factory=PrepConfig)
    docking: DockingConfig = field(default_factory=DockingConfig)
    fep: FEPConfig = field(default_factory=FEPConfig)
    abfe: ABFEConfig = field(default_factory=ABFEConfig)


_NESTED_TYPES: dict[str, type] = {
    "ServerConfig": ServerConfig,
    "PrepConfig": PrepConfig,
    "DockingConfig": DockingConfig,
    "FEPConfig": FEPConfig,
    "ABFEConfig": ABFEConfig,
}


def _build_dataclass(cls: type, data: dict[str, Any]) -> Any:
    """Recursively build a dataclass from a dict, ignoring unknown keys."""
    import dataclasses

    field_names = {f.name for f in dataclasses.fields(cls)}
    filtered = {}
    for k, v in data.items():
        if k not in field_names:
            continue
        fld = next(f for f in dataclasses.fields(cls) if f.name == k)
        # Resolve string type annotations to actual types
        fld_type = fld.type if isinstance(fld.type, type) else _NESTED_TYPES.get(str(fld.type))
        if fld_type is not None and dataclasses.is_dataclass(fld_type) and isinstance(v, dict):
            filtered[k] = _build_dataclass(fld_type, v)
        else:
            filtered[k] = v
    return cls(**filtered)


def load_config(path: str | Path) -> PipelineConfig:
    """Load pipeline configuration from a YAML file.

    Args:
        path: Path to the YAML config file.

    Returns:
        Populated PipelineConfig dataclass.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path) as f:
        raw = yaml.safe_load(f) or {}

    return _build_dataclass(PipelineConfig, raw)
