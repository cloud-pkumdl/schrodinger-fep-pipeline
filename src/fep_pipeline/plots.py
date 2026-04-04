"""QC plotting module for FEP+ calculations.

Generates publication-quality quality control plots:
- MBAR overlap matrix heatmap
- Replica exchange transition matrix heatmap
- Forward/reverse convergence plot
- Predicted vs experimental DDG correlation
- Per-edge hysteresis bar chart
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import matplotlib
import numpy as np

# Use non-interactive backend so plots work on headless servers
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from fep_pipeline.utils import logger

# QC threshold constants
MBAR_OVERLAP_GOOD = 0.10
MBAR_OVERLAP_BAD = 0.03
RE_EXCHANGE_GOOD = 0.15
RE_EXCHANGE_BAD = 0.05
FWD_REV_GAP_GOOD = 0.5
FWD_REV_GAP_BAD = 1.5
HYSTERESIS_1KBT = 0.6  # kcal/mol at 300K


def plot_mbar_overlap_matrix(
    overlap: np.ndarray,
    out_path: str | Path,
    title: str = "MBAR Overlap Matrix",
) -> Path:
    """Plot MBAR overlap matrix as an annotated heatmap.

    Args:
        overlap: Square matrix (n_lambda x n_lambda) of overlap values.
        out_path: Output file path for the figure.
        title: Plot title.

    Returns:
        Path to the saved figure.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = overlap.shape[0]

    # Red-yellow-green colormap: bad (red) -> marginal (yellow) -> good (green)
    cmap = LinearSegmentedColormap.from_list(
        "overlap_ryg",
        [(0.0, "#d32f2f"), (0.06, "#ff9800"), (0.20, "#4caf50"), (1.0, "#1b5e20")],
    )

    fig, ax = plt.subplots(figsize=(max(6, n * 0.5), max(5, n * 0.45)))
    im = ax.imshow(overlap, cmap=cmap, vmin=0, vmax=0.5, aspect="equal", origin="lower")
    plt.colorbar(im, ax=ax, label="Overlap", shrink=0.8)

    # Annotate cells
    for i in range(n):
        for j in range(n):
            val = overlap[i, j]
            if val < 0.001:
                continue
            color = "white" if val < 0.05 else "black"
            fontsize = max(5, min(8, 120 // n))
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=fontsize, color=color)

    ax.set_xlabel("Lambda State")
    ax.set_ylabel("Lambda State")
    ax.set_title(title)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))

    # Flag bad adjacent overlaps in the title
    bad_pairs = []
    for i in range(n - 1):
        if overlap[i, i + 1] < MBAR_OVERLAP_BAD:
            bad_pairs.append(f"{i}-{i + 1}")
    if bad_pairs:
        ax.set_title(f"{title}\n(BAD overlap at: {', '.join(bad_pairs)})", color="red")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved MBAR overlap plot to %s", out_path)
    return out_path


def plot_re_transition_matrix(
    transitions: np.ndarray,
    out_path: str | Path,
    title: str = "Replica Exchange Transition Matrix",
) -> Path:
    """Plot replica exchange transition probability matrix.

    Args:
        transitions: Square matrix (n_lambda x n_lambda) of transition probabilities.
        out_path: Output file path for the figure.
        title: Plot title.

    Returns:
        Path to the saved figure.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = transitions.shape[0]

    cmap = LinearSegmentedColormap.from_list(
        "re_ryg",
        [(0.0, "#d32f2f"), (0.071, "#ff9800"), (0.214, "#4caf50"), (1.0, "#1b5e20")],
    )

    fig, ax = plt.subplots(figsize=(max(6, n * 0.5), max(5, n * 0.45)))
    im = ax.imshow(transitions, cmap=cmap, vmin=0, vmax=0.7, aspect="equal", origin="lower")
    plt.colorbar(im, ax=ax, label="Transition Probability", shrink=0.8)

    # Annotate cells
    for i in range(n):
        for j in range(n):
            val = transitions[i, j]
            if val < 0.001:
                continue
            color = "white" if val < 0.05 else "black"
            fontsize = max(5, min(8, 120 // n))
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=fontsize, color=color)

    ax.set_xlabel("Lambda State")
    ax.set_ylabel("Lambda State")
    ax.set_title(title)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))

    # Flag bad neighbor exchanges
    bad_pairs = []
    for i in range(n - 1):
        if transitions[i, i + 1] < RE_EXCHANGE_BAD:
            bad_pairs.append(f"{i}-{i + 1}")
    if bad_pairs:
        ax.set_title(f"{title}\n(LOW exchange at: {', '.join(bad_pairs)})", color="red")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved RE transition plot to %s", out_path)
    return out_path


def plot_convergence(
    fractions: np.ndarray,
    forward_dg: np.ndarray,
    reverse_dg: np.ndarray,
    out_path: str | Path,
    title: str = "Forward/Reverse Convergence",
    forward_err: np.ndarray | None = None,
    reverse_err: np.ndarray | None = None,
) -> Path:
    """Plot forward/reverse convergence traces for a single edge.

    Args:
        fractions: Array of sample fractions (0 to 1).
        forward_dg: Forward cumulative DG estimates at each fraction.
        reverse_dg: Reverse cumulative DG estimates at each fraction.
        out_path: Output file path for the figure.
        title: Plot title.
        forward_err: Optional error bars for forward estimates.
        reverse_err: Optional error bars for reverse estimates.

    Returns:
        Path to the saved figure.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(fractions, forward_dg, "b-o", markersize=3, label="Forward", linewidth=1.5)
    ax.plot(fractions, reverse_dg, "r-s", markersize=3, label="Reverse", linewidth=1.5)

    if forward_err is not None:
        ax.fill_between(
            fractions,
            forward_dg - forward_err,
            forward_dg + forward_err,
            alpha=0.15,
            color="blue",
        )
    if reverse_err is not None:
        ax.fill_between(
            fractions,
            reverse_dg - reverse_err,
            reverse_dg + reverse_err,
            alpha=0.15,
            color="red",
        )

    # Compute final gap and annotate
    final_gap = abs(forward_dg[-1] - reverse_dg[-1])
    gap_color = "green" if final_gap < FWD_REV_GAP_GOOD else ("orange" if final_gap < FWD_REV_GAP_BAD else "red")
    ax.annotate(
        f"Final gap: {final_gap:.2f} kcal/mol",
        xy=(0.98, 0.02),
        xycoords="axes fraction",
        ha="right",
        va="bottom",
        fontsize=10,
        color=gap_color,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": gap_color},
    )

    ax.set_xlabel("Fraction of Samples")
    ax.set_ylabel("ΔG (kcal/mol)")
    ax.set_title(title)
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved convergence plot to %s", out_path)
    return out_path


def plot_ddg_correlation(
    exp_ddg: np.ndarray,
    pred_ddg: np.ndarray,
    out_path: str | Path,
    title: str = "Predicted vs Experimental ΔΔG",
    labels: Sequence[str] | None = None,
    uncertainties: np.ndarray | None = None,
) -> Path:
    """Plot predicted vs experimental DDG correlation.

    Args:
        exp_ddg: Experimental DDG values (kcal/mol).
        pred_ddg: Predicted DDG values (kcal/mol).
        out_path: Output file path for the figure.
        title: Plot title.
        labels: Optional ligand labels for each point.
        uncertainties: Optional prediction uncertainties for error bars.

    Returns:
        Path to the saved figure.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(7, 7))

    # Determine plot range
    all_vals = np.concatenate([exp_ddg, pred_ddg])
    margin = 1.0
    lo = np.floor(np.min(all_vals) - margin)
    hi = np.ceil(np.max(all_vals) + margin)

    # y=x line
    ax.plot([lo, hi], [lo, hi], "k-", linewidth=1, label="y = x")

    # +/- 1 kcal/mol bands
    ax.fill_between([lo, hi], [lo - 1, hi - 1], [lo + 1, hi + 1], alpha=0.10, color="green", label="±1 kcal/mol")
    ax.fill_between([lo, hi], [lo - 2, hi - 2], [lo + 2, hi + 2], alpha=0.05, color="orange", label="±2 kcal/mol")

    # Data points
    if uncertainties is not None:
        ax.errorbar(
            exp_ddg, pred_ddg, yerr=uncertainties, fmt="o", color="#1976d2",
            markersize=7, capsize=3, elinewidth=1, markeredgecolor="white", markeredgewidth=0.5,
        )
    else:
        ax.scatter(exp_ddg, pred_ddg, s=50, c="#1976d2", edgecolors="white", linewidths=0.5, zorder=5)

    # Label points
    if labels is not None:
        for i, lbl in enumerate(labels):
            ax.annotate(lbl, (exp_ddg[i], pred_ddg[i]), fontsize=7, textcoords="offset points", xytext=(5, 5))

    # Compute statistics
    n = len(exp_ddg)
    errors = pred_ddg - exp_ddg
    mue = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors**2)))
    ss_tot = float(np.sum((exp_ddg - np.mean(exp_ddg)) ** 2))
    ss_res = float(np.sum(errors**2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

    stats_text = f"N = {n}\nR² = {r2:.3f}\nRMSE = {rmse:.2f} kcal/mol\nMUE = {mue:.2f} kcal/mol"
    ax.text(
        0.05, 0.95, stats_text, transform=ax.transAxes, fontsize=10, va="top",
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "lightyellow", "edgecolor": "gray"},
    )

    ax.set_xlabel("Experimental ΔΔG (kcal/mol)")
    ax.set_ylabel("Predicted ΔΔG (kcal/mol)")
    ax.set_title(title)
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved DDG correlation plot to %s", out_path)
    return out_path


def plot_hysteresis(
    edge_labels: Sequence[str],
    hysteresis: np.ndarray,
    out_path: str | Path,
    title: str = "Per-Edge Hysteresis",
) -> Path:
    """Plot per-edge forward/reverse hysteresis as a bar chart.

    Args:
        edge_labels: Labels for each edge (e.g., "Lig A -> Lig B").
        hysteresis: Absolute |forward - reverse| values in kcal/mol.
        out_path: Output file path for the figure.
        title: Plot title.

    Returns:
        Path to the saved figure.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n = len(edge_labels)
    fig, ax = plt.subplots(figsize=(max(8, n * 0.8), 5))

    colors = ["#4caf50" if h < HYSTERESIS_1KBT else ("#ff9800" if h < 2 * HYSTERESIS_1KBT else "#d32f2f") for h in hysteresis]
    ax.bar(range(n), hysteresis, color=colors, edgecolor="white", linewidth=0.5)

    # 1 kBT threshold line
    ax.axhline(y=HYSTERESIS_1KBT, color="red", linestyle="--", linewidth=1.2, label=f"1 kBT ({HYSTERESIS_1KBT} kcal/mol)")

    ax.set_xticks(range(n))
    ax.set_xticklabels(edge_labels, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("|Forward - Reverse| (kcal/mol)")
    ax.set_title(title)
    ax.legend(loc="upper right")
    ax.grid(True, axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved hysteresis plot to %s", out_path)
    return out_path


# ---------------------------------------------------------------------------
# Mock data generators for testing and demonstration
# ---------------------------------------------------------------------------


def generate_mock_overlap_matrix(n_lambda: int = 11, quality: str = "good") -> np.ndarray:
    """Generate a mock MBAR overlap matrix for testing.

    Args:
        n_lambda: Number of lambda windows.
        quality: "good", "marginal", or "bad".

    Returns:
        Symmetric overlap matrix.
    """
    overlap = np.zeros((n_lambda, n_lambda))
    for i in range(n_lambda):
        overlap[i, i] = 1.0  # self-overlap placeholder (diagonal)

    if quality == "good":
        base_offdiag = 0.15
    elif quality == "marginal":
        base_offdiag = 0.06
    else:
        base_offdiag = 0.02

    rng = np.random.default_rng(42)
    for i in range(n_lambda):
        for j in range(i + 1, n_lambda):
            dist = abs(i - j)
            val = base_offdiag * np.exp(-0.8 * (dist - 1))
            val += rng.normal(0, 0.005)
            val = max(0, val)
            overlap[i, j] = val
            overlap[j, i] = val

    return overlap


def generate_mock_re_transitions(n_lambda: int = 11, quality: str = "good") -> np.ndarray:
    """Generate a mock replica exchange transition matrix.

    Args:
        n_lambda: Number of lambda windows.
        quality: "good", "marginal", or "bad".

    Returns:
        Transition probability matrix.
    """
    trans = np.zeros((n_lambda, n_lambda))

    if quality == "good":
        base_prob = 0.25
    elif quality == "marginal":
        base_prob = 0.10
    else:
        base_prob = 0.03

    rng = np.random.default_rng(42)
    for i in range(n_lambda):
        for j in range(i + 1, n_lambda):
            dist = abs(i - j)
            val = base_prob * np.exp(-1.5 * (dist - 1))
            val += rng.normal(0, 0.01)
            val = max(0, min(0.7, val))
            trans[i, j] = val
            trans[j, i] = val

    # Diagonal: remaining probability (stays in same state)
    for i in range(n_lambda):
        trans[i, i] = 1.0 - np.sum(trans[i, :])

    return trans


def generate_mock_convergence(quality: str = "good") -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate mock forward/reverse convergence data.

    Args:
        quality: "good", "marginal", or "bad".

    Returns:
        Tuple of (fractions, forward_dg, reverse_dg).
    """
    fractions = np.linspace(0.1, 1.0, 20)
    rng = np.random.default_rng(42)
    true_dg = -5.0

    if quality == "good":
        forward = true_dg + 0.8 * np.exp(-4 * fractions) + rng.normal(0, 0.05, len(fractions))
        reverse = true_dg - 0.6 * np.exp(-4 * fractions) + rng.normal(0, 0.05, len(fractions))
    elif quality == "marginal":
        forward = true_dg + 1.5 * np.exp(-2 * fractions) + rng.normal(0, 0.15, len(fractions))
        reverse = true_dg - 1.2 * np.exp(-2 * fractions) + rng.normal(0, 0.15, len(fractions))
    else:
        forward = true_dg + 2.0 * np.exp(-0.5 * fractions) + rng.normal(0, 0.3, len(fractions))
        reverse = true_dg - 2.5 * np.exp(-0.3 * fractions) + rng.normal(0, 0.3, len(fractions))

    return fractions, forward, reverse


def generate_mock_ddg_data(
    n_ligands: int = 6, quality: str = "good"
) -> tuple[np.ndarray, np.ndarray, list[str], np.ndarray]:
    """Generate mock DDG correlation data.

    Args:
        n_ligands: Number of ligands.
        quality: "good", "marginal", or "bad".

    Returns:
        Tuple of (exp_ddg, pred_ddg, labels, uncertainties).
    """
    rng = np.random.default_rng(42)
    labels = [f"Lig_{i + 1}" for i in range(n_ligands)]
    exp_ddg = rng.uniform(-3, 3, n_ligands)

    if quality == "good":
        noise = rng.normal(0, 0.3, n_ligands)
    elif quality == "marginal":
        noise = rng.normal(0, 1.0, n_ligands)
    else:
        noise = rng.normal(0, 2.5, n_ligands)

    pred_ddg = exp_ddg + noise
    uncertainties = np.abs(rng.normal(0.3, 0.1, n_ligands))
    return exp_ddg, pred_ddg, labels, uncertainties


def generate_mock_hysteresis(
    n_edges: int = 8, quality: str = "good"
) -> tuple[list[str], np.ndarray]:
    """Generate mock per-edge hysteresis data.

    Args:
        n_edges: Number of edges.
        quality: "good", "marginal", or "bad".

    Returns:
        Tuple of (edge_labels, hysteresis_values).
    """
    rng = np.random.default_rng(42)
    labels = [f"L{i} -> L{i + 1}" for i in range(n_edges)]

    if quality == "good":
        hysteresis = np.abs(rng.normal(0.2, 0.1, n_edges))
    elif quality == "marginal":
        hysteresis = np.abs(rng.normal(0.5, 0.2, n_edges))
    else:
        hysteresis = np.abs(rng.normal(1.0, 0.4, n_edges))

    return labels, hysteresis


def generate_qc_report(
    workdir: str | Path,
    *,
    use_mock: bool = False,
    mock_quality: str = "good",
) -> list[Path]:
    """Generate all QC plots for an FEP+ run.

    If use_mock is True, generates plots from mock data (useful for testing
    and demonstration without Schrödinger output files).

    When use_mock is False, attempts to parse FEP+ output files in workdir.
    This requires the Schrödinger Python API for SID file parsing.

    Args:
        workdir: Directory containing FEP+ output files (or destination for mock plots).
        use_mock: If True, use generated mock data instead of real FEP+ output.
        mock_quality: Quality level for mock data ("good", "marginal", "bad").

    Returns:
        List of Paths to generated plot files.
    """
    workdir = Path(workdir)
    plot_dir = workdir / "qc_plots"
    plot_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    if use_mock:
        logger.info("Generating QC report from mock data (quality=%s)", mock_quality)

        # MBAR overlap
        overlap = generate_mock_overlap_matrix(quality=mock_quality)
        generated.append(plot_mbar_overlap_matrix(overlap, plot_dir / "mbar_overlap.png"))

        # RE transitions
        trans = generate_mock_re_transitions(quality=mock_quality)
        generated.append(plot_re_transition_matrix(trans, plot_dir / "re_transitions.png"))

        # Convergence
        fracs, fwd, rev = generate_mock_convergence(quality=mock_quality)
        generated.append(plot_convergence(fracs, fwd, rev, plot_dir / "convergence.png"))

        # DDG correlation
        exp, pred, labels, unc = generate_mock_ddg_data(quality=mock_quality)
        generated.append(plot_ddg_correlation(exp, pred, plot_dir / "ddg_correlation.png", labels=labels, uncertainties=unc))

        # Hysteresis
        edge_labels, hyst = generate_mock_hysteresis(quality=mock_quality)
        generated.append(plot_hysteresis(edge_labels, hyst, plot_dir / "hysteresis.png"))

        logger.info("Generated %d QC plots in %s", len(generated), plot_dir)
    else:
        logger.info("Parsing FEP+ output files in %s", workdir)
        # Real data parsing requires Schrödinger Python API for SID files.
        # Look for common FEP+ output files:
        #   - *_overlap.csv or overlap data in SID files
        #   - *_results.csv for DDG data
        #   - *_convergence.csv for convergence data
        #
        # This is a placeholder for Schrödinger-specific parsing.
        # In production, use:
        #   from schrodinger.application.desmond import cms
        #   from schrodinger.application.scisol.fep import graph
        logger.warning(
            "Real FEP+ output parsing requires Schrödinger Python API. "
            "Use use_mock=True for demonstration plots, or run on a machine "
            "with $SCHRODINGER set."
        )

    return generated
