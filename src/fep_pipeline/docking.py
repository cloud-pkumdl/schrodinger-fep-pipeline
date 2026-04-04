"""Glide docking — grid generation and ligand docking."""

from __future__ import annotations

from pathlib import Path

from fep_pipeline.config import PipelineConfig
from fep_pipeline.utils import logger, scp_download, scp_upload, ssh_run


def run_docking(
    config: PipelineConfig,
    protein_mae: str | Path,
    ligands_mae: str | Path,
) -> str:
    """Run Glide docking: generate grid then dock ligands.

    Args:
        config: Pipeline configuration.
        protein_mae: Path to prepared protein MAE.
        ligands_mae: Path to prepared ligands MAE.

    Returns:
        Local path to the poseviewer output file.
    """
    srv = config.server
    protein_mae = Path(protein_mae)
    ligands_mae = Path(ligands_mae)

    logger.info("Uploading structures for docking")
    ssh_run(srv.host, f"mkdir -p '{srv.scratch}'")
    scp_upload(srv.host, protein_mae, f"{srv.scratch}/{protein_mae.name}")
    scp_upload(srv.host, ligands_mae, f"{srv.scratch}/{ligands_mae.name}")

    # Step 1: Generate receptor grid
    grid_job = f"{config.job_name}_grid"
    grid_zip = f"{grid_job}.zip"
    grid_input = _write_grid_input(config, protein_mae.name, grid_job)
    scp_upload(srv.host, grid_input, f"{srv.scratch}/{grid_input}")

    logger.info("Generating Glide grid")
    ssh_run(
        srv.host,
        f"cd '{srv.scratch}' && {srv.schrodinger}/glide {grid_input} -HOST localhost -WAIT",
    )

    # Step 2: Dock ligands
    dock_job = f"{config.job_name}_dock"
    pv_file = f"{dock_job}_pv.maegz"
    dock_input = _write_dock_input(config, grid_zip, ligands_mae.name, dock_job)
    scp_upload(srv.host, dock_input, f"{srv.scratch}/{dock_input}")

    logger.info("Running Glide docking (%s)", config.docking.precision)
    ssh_run(
        srv.host,
        f"cd '{srv.scratch}' && {srv.schrodinger}/glide {dock_input} -HOST localhost -WAIT",
    )

    # Download poseviewer file
    local_pv = str(Path(config.output_dir) / pv_file)
    logger.info("Downloading docking results: %s", pv_file)
    scp_download(srv.host, f"{srv.scratch}/{pv_file}", local_pv)

    return local_pv


def _write_grid_input(
    config: PipelineConfig,
    protein_file: str,
    job_name: str,
) -> str:
    """Write a Glide grid generation input file.

    Args:
        config: Pipeline configuration.
        protein_file: Protein MAE filename (remote).
        job_name: Grid job name.

    Returns:
        Local path to the written input file.
    """
    dc = config.docking
    content = f"""\
GRIDFILE   {job_name}.zip
JOBNAME    {job_name}
RECEP_FILE {protein_file}
"""
    if dc.grid_center:
        content += f"GRID_CENTER   {dc.grid_center[0]},{dc.grid_center[1]},{dc.grid_center[2]}\n"
    else:
        content += "GRID_CENTER   SELF\n"
    content += f"INNERBOX   {dc.grid_inner_box},{dc.grid_inner_box},{dc.grid_inner_box}\n"
    content += f"OUTERBOX   {dc.grid_outer_box},{dc.grid_outer_box},{dc.grid_outer_box}\n"

    input_file = f"{job_name}.in"
    Path(input_file).write_text(content)
    return input_file


def _write_dock_input(
    config: PipelineConfig,
    grid_file: str,
    ligands_file: str,
    job_name: str,
) -> str:
    """Write a Glide docking input file.

    Args:
        config: Pipeline configuration.
        grid_file: Grid ZIP filename (remote).
        ligands_file: Ligands MAE filename (remote).
        job_name: Docking job name.

    Returns:
        Local path to the written input file.
    """
    dc = config.docking
    content = f"""\
JOBNAME      {job_name}
GRIDFILE     {grid_file}
LIGANDFILE   {ligands_file}
PRECISION    {dc.precision}
POSES_PER_LIG {dc.poses_per_lig}
POSTDOCK_NPOSE 1
WRITE_XP_DESC False
"""

    input_file = f"{job_name}.in"
    Path(input_file).write_text(content)
    return input_file


def build_grid_cmd(
    schrodinger_path: str,
    input_file: str,
) -> list[str]:
    """Build a Glide grid generation command.

    Args:
        schrodinger_path: Path to Schrödinger installation.
        input_file: Grid input file.

    Returns:
        Command as list of strings.
    """
    return [f"{schrodinger_path}/glide", input_file, "-HOST", "localhost", "-WAIT"]


def build_dock_cmd(
    schrodinger_path: str,
    input_file: str,
) -> list[str]:
    """Build a Glide docking command.

    Args:
        schrodinger_path: Path to Schrödinger installation.
        input_file: Docking input file.

    Returns:
        Command as list of strings.
    """
    return [f"{schrodinger_path}/glide", input_file, "-HOST", "localhost", "-WAIT"]
