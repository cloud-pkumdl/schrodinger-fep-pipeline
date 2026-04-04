"""Ligand preparation — LigPrep wrapper for SMILES/SDF to 3D MAE."""

from __future__ import annotations

import csv
from pathlib import Path

from fep_pipeline.config import PipelineConfig
from fep_pipeline.utils import logger, scp_download, scp_upload, ssh_run


def read_smiles_file(path: str | Path) -> list[tuple[str, str]]:
    """Read a SMILES file (tab or space separated: SMILES name).

    Args:
        path: Path to .smi file.

    Returns:
        List of (smiles, name) tuples.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"SMILES file not found: {path}")

    compounds: list[tuple[str, str]] = []
    with open(path) as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if not row or row[0].startswith("#"):
                continue
            # Handle both tab and space delimited
            parts = row[0].split() if len(row) == 1 else row
            if len(parts) >= 2:
                compounds.append((parts[0].strip(), parts[1].strip()))
            elif len(parts) == 1:
                compounds.append((parts[0].strip(), f"lig_{len(compounds)}"))
    return compounds


def prepare_ligands(
    config: PipelineConfig,
    ligand_file: str | Path,
) -> str:
    """Run LigPrep on a SMILES or SDF file to generate 3D MAE structures.

    Args:
        config: Pipeline configuration.
        ligand_file: Path to input .smi or .sdf file.

    Returns:
        Local path to the prepared ligands MAE file.
    """
    ligand_file = Path(ligand_file)
    if not ligand_file.exists():
        raise FileNotFoundError(f"Ligand file not found: {ligand_file}")

    srv = config.server
    basename = ligand_file.stem
    remote_input = f"{srv.scratch}/{ligand_file.name}"
    output_mae = f"{basename}_prepared.maegz"
    remote_output = f"{srv.scratch}/{output_mae}"

    logger.info("Uploading %s to %s", ligand_file.name, srv.host)
    ssh_run(srv.host, f"mkdir -p '{srv.scratch}'")
    scp_upload(srv.host, ligand_file, remote_input)

    cmd = build_ligprep_cmd(
        srv.schrodinger,
        remote_input,
        remote_output,
        job_name=f"ligprep_{basename}",
        force_field=config.prep.force_field,
        ph=config.prep.ph,
    )
    cmd_str = " ".join(cmd)
    logger.info("Running LigPrep on %s", ligand_file.name)
    ssh_run(srv.host, cmd_str)

    local_output = str(Path(config.output_dir) / output_mae)
    logger.info("Downloading prepared ligands: %s", output_mae)
    scp_download(srv.host, remote_output, local_output)

    return local_output


def build_ligprep_cmd(
    schrodinger_path: str,
    input_file: str,
    output_file: str,
    *,
    job_name: str = "ligprep",
    force_field: str = "OPLS4",
    ph: float = 7.0,
    ph_tolerance: float = 1.0,
    max_stereo: int = 4,
) -> list[str]:
    """Build a LigPrep command line.

    Args:
        schrodinger_path: Path to Schrödinger installation.
        input_file: Input SMILES/SDF/MAE file.
        output_file: Output MAE file.
        job_name: Job name.
        force_field: Force field for optimization.
        ph: Target pH for ionization.
        ph_tolerance: pH tolerance for Epik.
        max_stereo: Max stereoisomers to generate.

    Returns:
        Command as list of strings.
    """
    cmd = [
        f"{schrodinger_path}/ligprep",
        "-JOBNAME",
        job_name,
        "-HOST",
        "localhost",
        "-bff",
        "14" if force_field == "OPLS4" else "16",
        "-epik",
        "-ph",
        str(ph),
        "-pht",
        str(ph_tolerance),
        "-s",
        str(max_stereo),
        "-ifile",
        input_file,
        "-ofile",
        output_file,
    ]
    return cmd
