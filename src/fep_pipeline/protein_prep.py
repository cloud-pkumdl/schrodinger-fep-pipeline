"""Protein preparation — PrepWizard wrapper for PDB processing."""

from __future__ import annotations

from pathlib import Path

from fep_pipeline.config import PipelineConfig
from fep_pipeline.utils import logger, schrodinger_run, scp_download, scp_upload, ssh_run


def prepare_protein(config: PipelineConfig, pdb_path: str | Path) -> str:
    """Run PrepWizard on a PDB file to produce a prepared MAE structure.

    Steps:
        1. Upload PDB to remote server
        2. Run prepwizard with configured options
        3. Download prepared MAE file

    Args:
        config: Pipeline configuration.
        pdb_path: Path to input PDB file.

    Returns:
        Local path to the prepared MAE file.
    """
    pdb_path = Path(pdb_path)
    if not pdb_path.exists():
        raise FileNotFoundError(f"PDB file not found: {pdb_path}")

    srv = config.server
    basename = pdb_path.stem
    remote_pdb = f"{srv.scratch}/{pdb_path.name}"
    output_mae = f"{basename}_prepared.mae"
    remote_output = f"{srv.scratch}/{output_mae}"

    logger.info("Uploading %s to %s", pdb_path.name, srv.host)
    ssh_run(srv.host, f"mkdir -p '{srv.scratch}'")
    scp_upload(srv.host, pdb_path, remote_pdb)

    # Build prepwizard command
    cmd_parts = [
        f"{srv.schrodinger}/utilities/prepwizard",
        f"-JOBNAME prep_{basename}",
        "-HOST localhost",
    ]
    prep = config.prep
    if prep.fill_loops:
        cmd_parts.append("-fillloops")
    if prep.fill_side_chains:
        cmd_parts.append("-fillsidechains")
    if prep.minimize_hydrogens:
        cmd_parts.append("-rehtreat")
    cmd_parts.append(f"-f {prep.force_field}")
    cmd_parts.append(f"-watdist {prep.water_dist}")
    cmd_parts.append(f"'{remote_pdb}'")
    cmd_parts.append(f"'{remote_output}'")

    cmd = " ".join(cmd_parts)
    logger.info("Running PrepWizard on %s", pdb_path.name)
    schrodinger_run(srv.schrodinger, srv.host, cmd)

    # Download result
    local_output = str(Path(config.output_dir) / output_mae)
    logger.info("Downloading prepared structure: %s", output_mae)
    scp_download(srv.host, remote_output, local_output)

    return local_output


def build_prepwizard_cmd(
    schrodinger_path: str,
    input_file: str,
    output_file: str,
    *,
    job_name: str = "prep",
    force_field: str = "OPLS4",
    fill_loops: bool = True,
    fill_side_chains: bool = True,
    water_dist: float = 5.0,
) -> list[str]:
    """Build a prepwizard command line (for scripting or dry-run).

    Args:
        schrodinger_path: Path to Schrödinger installation.
        input_file: Input PDB/MAE file.
        output_file: Output MAE file.
        job_name: Job name prefix.
        force_field: Force field for minimization.
        fill_loops: Fill missing loops.
        fill_side_chains: Fill missing side chains.
        water_dist: Distance cutoff for water removal (Å).

    Returns:
        Command as list of strings.
    """
    cmd = [
        f"{schrodinger_path}/utilities/prepwizard",
        "-JOBNAME",
        job_name,
        "-HOST",
        "localhost",
    ]
    if fill_loops:
        cmd.append("-fillloops")
    if fill_side_chains:
        cmd.append("-fillsidechains")
    cmd.extend(["-rehtreat", "-f", force_field])
    cmd.extend(["-watdist", str(water_dist)])
    cmd.extend([input_file, output_file])
    return cmd
