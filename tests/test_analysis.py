"""Tests for FEP+ result analysis and QC metrics."""

from __future__ import annotations

from pathlib import Path

import pytest

from fep_pipeline.analysis import (
    FEPResult,
    QCMetrics,
    check_qc_thresholds,
    compute_qc_metrics,
    format_results_table,
    parse_fep_summary_csv,
)


def test_parse_fep_summary_csv(sample_csv_file: Path) -> None:
    """Parse a well-formed FEP+ summary CSV."""
    results = parse_fep_summary_csv(sample_csv_file)
    assert len(results) == 6
    assert results[0].ligand_name == "benzene"
    assert results[0].predicted_dg == pytest.approx(-5.10)
    assert results[0].experimental_dg == pytest.approx(-5.19)
    assert results[0].uncertainty == pytest.approx(0.15)


def test_parse_csv_missing_file() -> None:
    """Raise FileNotFoundError for missing CSV."""
    with pytest.raises(FileNotFoundError):
        parse_fep_summary_csv("/nonexistent/summary.csv")


def test_compute_qc_metrics(sample_csv_file: Path) -> None:
    """Compute QC metrics from parsed results."""
    results = parse_fep_summary_csv(sample_csv_file)
    metrics = compute_qc_metrics(results)
    assert metrics.num_ligands == 6
    assert metrics.mean_unsigned_error is not None
    assert metrics.mean_unsigned_error >= 0
    assert metrics.rmse is not None
    assert metrics.rmse >= 0
    assert metrics.correlation_r2 is not None


def test_compute_qc_metrics_good_predictions() -> None:
    """Good predictions yield low MUE and high R²."""
    results = [
        FEPResult("a", predicted_dg=-5.0, experimental_dg=-5.0),
        FEPResult("b", predicted_dg=-6.0, experimental_dg=-6.0),
        FEPResult("c", predicted_dg=-4.0, experimental_dg=-4.0),
    ]
    metrics = compute_qc_metrics(results)
    assert metrics.mean_unsigned_error == pytest.approx(0.0)
    assert metrics.rmse == pytest.approx(0.0)
    assert metrics.correlation_r2 == pytest.approx(1.0)


def test_compute_qc_metrics_insufficient_data() -> None:
    """Single result can't compute metrics."""
    results = [FEPResult("a", predicted_dg=-5.0, experimental_dg=-5.0)]
    metrics = compute_qc_metrics(results)
    assert metrics.mean_unsigned_error is None


def test_check_qc_thresholds_pass() -> None:
    """Good metrics produce no warnings."""
    metrics = QCMetrics(
        num_ligands=10,
        mean_unsigned_error=0.8,
        rmse=1.0,
        correlation_r2=0.7,
    )
    warnings = check_qc_thresholds(metrics)
    assert warnings == []


def test_check_qc_thresholds_fail() -> None:
    """Bad metrics produce warnings."""
    metrics = QCMetrics(
        num_ligands=5,
        mean_unsigned_error=2.0,
        rmse=3.0,
        correlation_r2=0.1,
        poor_overlap_edges=3,
        max_hysteresis=1.5,
    )
    warnings = check_qc_thresholds(metrics)
    assert len(warnings) == 5  # MUE, RMSE, R², overlap, hysteresis


def test_format_results_table() -> None:
    """Format results into a readable table."""
    results = [
        FEPResult("benzene", predicted_dg=-5.10, experimental_dg=-5.19, uncertainty=0.15),
        FEPResult("toluene", predicted_dg=-5.60, experimental_dg=-5.49, uncertainty=0.20),
    ]
    table = format_results_table(results)
    assert "benzene" in table
    assert "toluene" in table
    assert "Pred" in table
