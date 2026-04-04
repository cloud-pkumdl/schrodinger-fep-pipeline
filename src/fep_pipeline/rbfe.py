"""RBFE (Relative Binding Free Energy) — FEP+ workflow wrapper."""

from __future__ import annotations

from pathlib import Path

from fep_pipeline.config import PipelineConfig
from fep_pipeline.utils import logger, scp_download, scp_upload, ssh_run


def run_rbfe(
    config: PipelineConfig,
    poseviewer_file: str | Path,
    *,
    prepare_only: bool = False,
) -> str:
    """Run FEP+ relative binding free energy calculation.

    Args:
        config: Pipeline configuration.
        poseviewer_file: Poseviewer MAE file (protein + docked ligands).
        prepare_only: If True, only generate the perturbation map without MD.

    Returns:
        Local path to the output FMP file.
    """
    poseviewer_file = Path(poseviewer_file)
    if not poseviewer_file.exists():
        raise FileNotFoundError(f"Poseviewer file not found: {poseviewer_file}")

    srv = config.server
    fep_cfg = config.fep
    remote_input = f"{srv.scratch}/{poseviewer_file.name}"

    logger.info("Uploading %s for FEP+", poseviewer_file.name)
    ssh_run(srv.host, f"mkdir -p '{srv.scratch}'")
    scp_upload(srv.host, poseviewer_file, remote_input)

    # Build fep_plus command
    cmd = build_fep_plus_cmd(
        srv.schrodinger,
        remote_input,
        job_name=config.job_name,
        sim_time=fep_cfg.sim_time,
        lambda_windows=fep_cfg.lambda_windows,
        force_field=fep_cfg.force_field,
        gpu_id=config.gpu_id,
        prepare_only=prepare_only,
    )
    cmd_str = " ".join(cmd)

    if prepare_only:
        logger.info("Running FEP+ in prepare-only mode")
    else:
        logger.info(
            "Running FEP+ (%d ps/lambda x %d lambda windows)",
            fep_cfg.sim_time,
            fep_cfg.lambda_windows,
        )

    ssh_run(srv.host, f"cd '{srv.scratch}' && {cmd_str}")

    # Download FMP result
    fmp_file = f"{config.job_name}.fmp"
    local_fmp = str(Path(config.output_dir) / fmp_file)
    logger.info("Downloading FMP: %s", fmp_file)
    scp_download(srv.host, f"{srv.scratch}/{fmp_file}", local_fmp)

    return local_fmp


def build_fep_plus_cmd(
    schrodinger_path: str,
    input_file: str,
    *,
    job_name: str = "fep_job",
    sim_time: int = 5000,
    lambda_windows: int = 12,
    force_field: str = "OPLS4",
    gpu_id: int = 1,
    prepare_only: bool = False,
) -> list[str]:
    """Build an fep_plus command line.

    Args:
        schrodinger_path: Path to Schrödinger installation.
        input_file: Poseviewer MAE file.
        job_name: FEP+ job name.
        sim_time: MD simulation time per lambda window (ps).
        lambda_windows: Number of lambda windows.
        force_field: Force field (OPLS4 or OPLS5).
        gpu_id: GPU device ID.
        prepare_only: Only prepare input, skip MD.

    Returns:
        Command as list of strings.
    """
    cmd = [
        f"CUDA_VISIBLE_DEVICES={gpu_id}",
        f"{schrodinger_path}/fep_plus",
        "-HOST",
        "localhost",
        "-SUBHOST",
        "localhost",
        "-JOBNAME",
        job_name,
        "-ff",
        force_field,
        "-ppj",
        "1",
    ]
    if prepare_only:
        cmd.append("-prepare")
    cmd.append(input_file)
    return cmd
