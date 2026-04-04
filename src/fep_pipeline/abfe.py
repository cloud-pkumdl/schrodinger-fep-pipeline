"""ABFE (Absolute Binding Free Energy) — fep_absolute_binding wrapper."""

from __future__ import annotations

from pathlib import Path

from fep_pipeline.config import PipelineConfig
from fep_pipeline.utils import logger, scp_download, scp_upload, ssh_run


def run_abfe(
    config: PipelineConfig,
    complex_file: str | Path,
    *,
    prepare_only: bool = False,
) -> str:
    """Run absolute binding free energy calculation.

    Workflow:
        1. Complex leg: protein-ligand complex → anneal → dissociate
        2. Solvent leg: ligand in solvent → anneal → vanish
        3. ΔG_bind = ΔG_complex - ΔG_solvent

    Args:
        config: Pipeline configuration.
        complex_file: Protein-ligand complex MAE (poseviewer format).
        prepare_only: If True, only prepare input without running MD.

    Returns:
        Local path to the output FMP file.
    """
    complex_file = Path(complex_file)
    if not complex_file.exists():
        raise FileNotFoundError(f"Complex file not found: {complex_file}")

    srv = config.server
    abfe_cfg = config.abfe
    remote_input = f"{srv.scratch}/{complex_file.name}"

    logger.info("Uploading %s for ABFE", complex_file.name)
    ssh_run(srv.host, f"mkdir -p '{srv.scratch}'")
    scp_upload(srv.host, complex_file, remote_input)

    cmd = build_abfe_cmd(
        srv.schrodinger,
        remote_input,
        job_name=config.job_name,
        fep_sim_time=abfe_cfg.fep_sim_time,
        md_sim_time=abfe_cfg.md_sim_time,
        force_field=abfe_cfg.force_field,
        gpu_id=config.gpu_id,
        multi_gpus=config.multi_gpus,
        prepare_only=prepare_only,
    )
    cmd_str = " ".join(cmd)

    if prepare_only:
        logger.info("Running ABFE in prepare-only mode")
    else:
        logger.info(
            "Running ABFE (FEP %d ps, MD %d ps)",
            abfe_cfg.fep_sim_time,
            abfe_cfg.md_sim_time,
        )

    ssh_run(srv.host, f"cd '{srv.scratch}' && {cmd_str}")

    # Download result
    fmp_file = f"{config.job_name}-out.fmp"
    local_fmp = str(Path(config.output_dir) / fmp_file)
    logger.info("Downloading ABFE result: %s", fmp_file)
    scp_download(srv.host, f"{srv.scratch}/{fmp_file}", local_fmp)

    return local_fmp


def build_abfe_cmd(
    schrodinger_path: str,
    input_file: str,
    *,
    job_name: str = "abfe_job",
    fep_sim_time: int = 5000,
    md_sim_time: int = 500,
    force_field: str = "OPLS4",
    gpu_id: int = 1,
    multi_gpus: str = "",
    prepare_only: bool = False,
) -> list[str]:
    """Build an fep_absolute_binding command line.

    Args:
        schrodinger_path: Path to Schrödinger installation.
        input_file: Protein-ligand complex MAE file.
        job_name: Job name.
        fep_sim_time: FEP simulation time (ps).
        md_sim_time: MD equilibration time (ps).
        force_field: Force field (OPLS4 or OPLS5).
        gpu_id: GPU device ID (used when multi_gpus is empty).
        multi_gpus: Comma-separated GPU IDs for multi-GPU runs.
        prepare_only: Only prepare input, skip MD.

    Returns:
        Command as list of strings.
    """
    if multi_gpus:
        gpu_env = f"CUDA_VISIBLE_DEVICES={multi_gpus}"
        gpu_count = len(multi_gpus.split(","))
        subhost = f"localhost:{gpu_count}"
    else:
        gpu_env = f"CUDA_VISIBLE_DEVICES={gpu_id}"
        subhost = "localhost:1"

    cmd = [
        gpu_env,
        f"{schrodinger_path}/fep_absolute_binding",
        input_file,
        "-ff",
        force_field,
        "-fep-sim-time",
        str(fep_sim_time),
        "-md-sim-time",
        str(md_sim_time),
        "-HOST",
        "localhost",
        "-SUBHOST",
        subhost,
        "-JOBNAME",
        job_name,
    ]
    if prepare_only:
        cmd.append("-prepare")
    return cmd
