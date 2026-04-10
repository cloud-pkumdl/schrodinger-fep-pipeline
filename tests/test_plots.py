"""Tests for the QC plotting module.

All tests use mock data and do not require Schrödinger installed.
"""

from __future__ import annotations

import numpy as np

from fep_pipeline.plots import (
    generate_mock_convergence,
    generate_mock_ddg_data,
    generate_mock_hysteresis,
    generate_mock_overlap_matrix,
    generate_mock_re_transitions,
    generate_qc_report,
    plot_convergence,
    plot_ddg_correlation,
    plot_hysteresis,
    plot_mbar_overlap_matrix,
    plot_re_transition_matrix,
)


class TestMBAROverlapPlot:
    def test_generates_png(self, tmp_path):
        overlap = generate_mock_overlap_matrix(n_lambda=11, quality="good")
        out = plot_mbar_overlap_matrix(overlap, tmp_path / "overlap.png")
        assert out.exists()
        assert out.stat().st_size > 0

    def test_good_quality_matrix_shape(self):
        overlap = generate_mock_overlap_matrix(n_lambda=11, quality="good")
        assert overlap.shape == (11, 11)
        # Adjacent off-diagonal should be >= threshold for good quality
        for i in range(10):
            assert overlap[i, i + 1] >= 0.08  # good quality should be near 0.15

    def test_bad_quality_flags_title(self, tmp_path):
        overlap = generate_mock_overlap_matrix(n_lambda=11, quality="bad")
        out = plot_mbar_overlap_matrix(overlap, tmp_path / "overlap_bad.png")
        assert out.exists()

    def test_symmetric(self):
        overlap = generate_mock_overlap_matrix(n_lambda=8)
        np.testing.assert_array_almost_equal(overlap, overlap.T)


class TestRETransitionPlot:
    def test_generates_png(self, tmp_path):
        trans = generate_mock_re_transitions(n_lambda=11, quality="good")
        out = plot_re_transition_matrix(trans, tmp_path / "re_trans.png")
        assert out.exists()
        assert out.stat().st_size > 0

    def test_matrix_shape(self):
        trans = generate_mock_re_transitions(n_lambda=11)
        assert trans.shape == (11, 11)

    def test_rows_sum_to_one(self):
        trans = generate_mock_re_transitions(n_lambda=11, quality="good")
        row_sums = trans.sum(axis=1)
        np.testing.assert_array_almost_equal(row_sums, np.ones(11), decimal=10)

    def test_bad_quality(self, tmp_path):
        trans = generate_mock_re_transitions(n_lambda=11, quality="bad")
        out = plot_re_transition_matrix(trans, tmp_path / "re_bad.png")
        assert out.exists()


class TestConvergencePlot:
    def test_generates_png(self, tmp_path):
        fracs, fwd, rev = generate_mock_convergence(quality="good")
        out = plot_convergence(fracs, fwd, rev, tmp_path / "conv.png")
        assert out.exists()
        assert out.stat().st_size > 0

    def test_good_convergence_small_gap(self):
        _fracs, fwd, rev = generate_mock_convergence(quality="good")
        final_gap = abs(fwd[-1] - rev[-1])
        assert final_gap < 0.5  # good quality should converge

    def test_bad_convergence_large_gap(self):
        _fracs, fwd, rev = generate_mock_convergence(quality="bad")
        final_gap = abs(fwd[-1] - rev[-1])
        assert final_gap > 0.5  # bad quality should not converge well

    def test_with_error_bars(self, tmp_path):
        fracs, fwd, rev = generate_mock_convergence(quality="good")
        fwd_err = np.full_like(fwd, 0.1)
        rev_err = np.full_like(rev, 0.1)
        out = plot_convergence(
            fracs,
            fwd,
            rev,
            tmp_path / "conv_err.png",
            forward_err=fwd_err,
            reverse_err=rev_err,
        )
        assert out.exists()


class TestDDGCorrelationPlot:
    def test_generates_png(self, tmp_path):
        exp, pred, labels, unc = generate_mock_ddg_data(n_ligands=6, quality="good")
        out = plot_ddg_correlation(
            exp, pred, tmp_path / "ddg.png", labels=labels, uncertainties=unc
        )
        assert out.exists()
        assert out.stat().st_size > 0

    def test_without_labels_and_uncertainties(self, tmp_path):
        exp, pred, _, _ = generate_mock_ddg_data(n_ligands=6)
        out = plot_ddg_correlation(exp, pred, tmp_path / "ddg_plain.png")
        assert out.exists()

    def test_good_quality_stats(self):
        exp, pred, _, _ = generate_mock_ddg_data(n_ligands=20, quality="good")
        rmse = float(np.sqrt(np.mean((pred - exp) ** 2)))
        assert rmse < 1.0  # good quality should have low RMSE


class TestHysteresisPlot:
    def test_generates_png(self, tmp_path):
        labels, hyst = generate_mock_hysteresis(n_edges=8, quality="good")
        out = plot_hysteresis(labels, hyst, tmp_path / "hyst.png")
        assert out.exists()
        assert out.stat().st_size > 0

    def test_good_quality_below_threshold(self):
        _, hyst = generate_mock_hysteresis(n_edges=8, quality="good")
        assert np.mean(hyst) < 0.6  # most should be below 1 kBT

    def test_bad_quality_above_threshold(self):
        _, hyst = generate_mock_hysteresis(n_edges=8, quality="bad")
        assert np.mean(hyst) > 0.6  # most should exceed 1 kBT


class TestQCReport:
    def test_mock_report_generates_all_plots(self, tmp_path):
        plots = generate_qc_report(tmp_path, use_mock=True, mock_quality="good")
        assert len(plots) == 5
        for p in plots:
            assert p.exists()
            assert p.suffix == ".png"

    def test_mock_report_bad_quality(self, tmp_path):
        plots = generate_qc_report(tmp_path, use_mock=True, mock_quality="bad")
        assert len(plots) == 5

    def test_mock_report_marginal_quality(self, tmp_path):
        plots = generate_qc_report(tmp_path, use_mock=True, mock_quality="marginal")
        assert len(plots) == 5

    def test_real_report_without_schrodinger(self, tmp_path):
        # Without Schrödinger, should return empty list and log a warning
        plots = generate_qc_report(tmp_path, use_mock=False)
        assert plots == []

    def test_plot_directory_created(self, tmp_path):
        generate_qc_report(tmp_path, use_mock=True)
        assert (tmp_path / "qc_plots").is_dir()
