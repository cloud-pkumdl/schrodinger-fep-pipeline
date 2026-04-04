"""Result parsing and QC analysis for FEP+ calculations."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from fep_pipeline.utils import logger


@dataclass
class FEPResult:
    """Single ligand FEP result."""

    ligand_name: str
    predicted_dg: float
    predicted_ddg: float | None = None
    experimental_dg: float | None = None
    uncertainty: float | None = None


@dataclass
class QCMetrics:
    """Quality control metrics for an FEP+ run."""

    num_ligands: int = 0
    num_edges: int = 0
    mean_unsigned_error: float | None = None
    rmse: float | None = None
    correlation_r2: float | None = None
    max_hysteresis: float | None = None
    poor_overlap_edges: int = 0


def parse_fep_summary_csv(path: str | Path) -> list[FEPResult]:
    """Parse an FEP+ summary CSV file into structured results.

    The CSV format typically has columns:
        Title, FEP+ dG (kcal/mol), FEP+ ddG (kcal/mol), Uncertainty, ...

    Args:
        path: Path to the FEP+ summary CSV file.

    Returns:
        List of FEPResult objects.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Summary CSV not found: {path}")

    results: list[FEPResult] = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = _get_field(row, ["Title", "Ligand", "Name", "title", "ligand"])
            dg = _get_float(row, ["FEP+ dG (kcal/mol)", "dG", "pred_dg", "DG"])
            ddg = _get_float(row, ["FEP+ ddG (kcal/mol)", "ddG", "pred_ddg", "DDG"])
            unc = _get_float(row, ["Uncertainty", "uncertainty", "Error", "error"])
            exp = _get_float(row, ["Exp. dG (kcal/mol)", "exp_dg", "Experimental"])

            if name is not None and dg is not None:
                results.append(
                    FEPResult(
                        ligand_name=name,
                        predicted_dg=dg,
                        predicted_ddg=ddg,
                        experimental_dg=exp,
                        uncertainty=unc,
                    )
                )

    logger.info("Parsed %d results from %s", len(results), path.name)
    return results


def compute_qc_metrics(results: list[FEPResult]) -> QCMetrics:
    """Compute QC metrics from FEP results that have experimental data.

    Args:
        results: List of FEPResult with experimental_dg populated.

    Returns:
        QCMetrics with computed statistics.
    """
    paired = [
        (r.predicted_dg, r.experimental_dg) for r in results if r.experimental_dg is not None
    ]
    metrics = QCMetrics(num_ligands=len(results))

    if len(paired) < 2:
        logger.warning("Not enough paired data for QC metrics (need ≥2, got %d)", len(paired))
        return metrics

    pred = [p[0] for p in paired]
    exp = [p[1] for p in paired]
    n = len(paired)

    # MUE
    errors = [abs(p - e) for p, e in zip(pred, exp, strict=True)]
    metrics.mean_unsigned_error = sum(errors) / n

    # RMSE
    sq_errors = [(p - e) ** 2 for p, e in zip(pred, exp, strict=True)]
    metrics.rmse = (sum(sq_errors) / n) ** 0.5

    # R²
    mean_exp = sum(exp) / n
    ss_tot = sum((e - mean_exp) ** 2 for e in exp)
    ss_res = sum((e - p) ** 2 for p, e in zip(pred, exp, strict=True))
    metrics.correlation_r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else None

    # Check uncertainties
    high_unc = [r for r in results if r.uncertainty is not None and r.uncertainty > 1.0]
    if high_unc:
        logger.warning(
            "%d ligands have uncertainty > 1.0 kcal/mol: %s",
            len(high_unc),
            [r.ligand_name for r in high_unc],
        )

    return metrics


def parse_fmp_log(log_path: str | Path) -> dict[str, str]:
    """Extract key information from an FEP+ log file.

    Args:
        log_path: Path to the FEP+ log file.

    Returns:
        Dict with extracted info (job_name, status, num_edges, etc.).
    """
    log_path = Path(log_path)
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")

    info: dict[str, str] = {}
    text = log_path.read_text()

    # Extract job status
    if "Job completed" in text or "Finished" in text:
        info["status"] = "completed"
    elif "FAILED" in text or "Error" in text:
        info["status"] = "failed"
    else:
        info["status"] = "unknown"

    # Extract edge count
    edge_match = re.search(r"(\d+)\s+edges?", text)
    if edge_match:
        info["num_edges"] = edge_match.group(1)

    # Extract node count
    node_match = re.search(r"(\d+)\s+nodes?", text)
    if node_match:
        info["num_nodes"] = node_match.group(1)

    return info


def check_qc_thresholds(
    metrics: QCMetrics,
    *,
    max_mue: float = 1.5,
    max_rmse: float = 2.0,
    min_r2: float = 0.3,
) -> list[str]:
    """Check QC metrics against standard thresholds.

    Based on FEP best practices (Mey et al., LiveCoMS 2020):
    - MUE should be < 1.5 kcal/mol for useful predictions
    - RMSE should be < 2.0 kcal/mol
    - R² should be > 0.3 for meaningful correlation

    Args:
        metrics: Computed QC metrics.
        max_mue: Maximum acceptable MUE (kcal/mol).
        max_rmse: Maximum acceptable RMSE (kcal/mol).
        min_r2: Minimum acceptable R².

    Returns:
        List of warning strings (empty if all pass).
    """
    warnings: list[str] = []

    if metrics.mean_unsigned_error is not None and metrics.mean_unsigned_error > max_mue:
        warnings.append(f"MUE ({metrics.mean_unsigned_error:.2f}) exceeds threshold ({max_mue})")

    if metrics.rmse is not None and metrics.rmse > max_rmse:
        warnings.append(f"RMSE ({metrics.rmse:.2f}) exceeds threshold ({max_rmse})")

    if metrics.correlation_r2 is not None and metrics.correlation_r2 < min_r2:
        warnings.append(f"R² ({metrics.correlation_r2:.2f}) below threshold ({min_r2})")

    if metrics.poor_overlap_edges > 0:
        warnings.append(f"{metrics.poor_overlap_edges} edges with poor overlap (< 0.03)")

    if metrics.max_hysteresis is not None and metrics.max_hysteresis > 0.6:
        warnings.append(f"Max hysteresis ({metrics.max_hysteresis:.2f} kcal/mol) exceeds 1 kBT")

    return warnings


def format_results_table(results: list[FEPResult]) -> str:
    """Format FEP results as a simple text table.

    Args:
        results: List of FEPResult objects.

    Returns:
        Formatted table string.
    """
    lines = [
        f"{'Ligand':<20} {'Pred ΔG':>10} {'Exp ΔG':>10} {'Error':>10} {'Unc':>8}",
        "-" * 62,
    ]
    for r in results:
        exp_str = (
            f"{r.experimental_dg:>10.2f}" if r.experimental_dg is not None else f"{'N/A':>10}"
        )
        err_str = (
            f"{abs(r.predicted_dg - r.experimental_dg):>10.2f}"
            if r.experimental_dg is not None
            else f"{'N/A':>10}"
        )
        unc_str = f"{r.uncertainty:>8.2f}" if r.uncertainty is not None else f"{'N/A':>8}"
        lines.append(f"{r.ligand_name:<20} {r.predicted_dg:>10.2f} {exp_str} {err_str} {unc_str}")
    return "\n".join(lines)


def _get_field(row: dict[str, str], keys: list[str]) -> str | None:
    """Try multiple column names to find a field value."""
    for k in keys:
        if k in row and row[k].strip():
            return row[k].strip()
    return None


def _get_float(row: dict[str, str], keys: list[str]) -> float | None:
    """Try multiple column names to find a float value."""
    val = _get_field(row, keys)
    if val is None:
        return None
    try:
        return float(val)
    except ValueError:
        return None
