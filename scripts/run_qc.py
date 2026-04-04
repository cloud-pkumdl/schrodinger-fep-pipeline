#!/usr/bin/env python3
"""Extract real QC data from FEP+ fmp and generate publication-quality plots.

Run with: $SCHRODINGER/run python3 fep_qc_real.py <fmp_file> <output_dir>
"""
import math
import os
import sys
from pathlib import Path

from schrodinger.application.scisol.fep import graph

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

EXP_DG_ABS = {
    "benzene": -5.19, "toluene": -5.49, "ethylbenzene": -5.07,
    "p-xylene": -5.96, "chlorobenzene": -5.42, "phenol": -4.73,
}
REF_LIGAND = "toluene"


def parse_fmp(fmp_path):
    g = graph.Graph.deserialize(str(fmp_path))
    ref_exp = EXP_DG_ABS.get(REF_LIGAND, -5.49)

    nodes = []
    for n in g.nodes_iter():
        sid = n.short_id
        try:
            name = n.struc.property.get("s_m_title", sid)
        except Exception:
            name = sid
        dg_str = str(n.get_leg_dg_by_name("binding"))
        parts = dg_str.split("+-")
        val = float(parts[0])
        err = float(parts[1]) if len(parts) > 1 else 0.0
        exp_ddg = EXP_DG_ABS.get(name, None)
        if exp_ddg is not None:
            exp_ddg = exp_ddg - ref_exp
        nodes.append({"name": name, "sid": sid, "pred_ddg": val, "pred_err": err, "exp_ddg": exp_ddg})

    edges = []
    for e in g.edges_iter():
        n1, n2 = e.nodes
        try:
            name1 = n1.struc.property.get("s_m_title", n1.short_id)
            name2 = n2.struc.property.get("s_m_title", n2.short_id)
        except Exception:
            name1, name2 = n1.short_id, n2.short_id

        legs = {}
        for leg in e.get_leg_names():
            try:
                dg_str = str(e.get_leg_dg_by_name(leg))
                parts = dg_str.split("+-")
                legs[leg] = {"dg": float(parts[0]), "err": float(parts[1]) if len(parts) > 1 else 0.0}
            except Exception:
                legs[leg] = None

        edges.append({
            "name1": name1, "name2": name2,
            "sid1": n1.short_id, "sid2": n2.short_id,
            "completed": e.is_fep_completed, "bad": e.bad_edge, "legs": legs,
        })

    return nodes, edges


def plot_ddg_correlation(nodes, out_dir):
    paired = [(n["pred_ddg"], n["exp_ddg"], n["pred_err"], n["name"])
              for n in nodes if n["exp_ddg"] is not None]
    if len(paired) < 2:
        return

    pred = np.array([p[0] for p in paired])
    exp = np.array([p[1] for p in paired])
    errs = np.array([p[2] for p in paired])
    names = [p[3] for p in paired]

    fig, ax = plt.subplots(figsize=(7, 7))
    all_vals = np.concatenate([pred, exp])
    lo, hi = np.floor(np.min(all_vals) - 1.5), np.ceil(np.max(all_vals) + 1.5)

    ax.plot([lo, hi], [lo, hi], "k-", linewidth=1, label="y = x")
    ax.fill_between([lo, hi], [lo - 1, hi - 1], [lo + 1, hi + 1], alpha=0.10, color="green", label=u"\u00b11 kcal/mol")

    ax.errorbar(exp, pred, yerr=errs, fmt="o", color="#1976d2", markersize=9, capsize=4,
                elinewidth=1.5, markeredgecolor="white", markeredgewidth=0.8, zorder=5)

    for i, name in enumerate(names):
        ax.annotate(name, (exp[i], pred[i]), fontsize=9, textcoords="offset points", xytext=(6, 6))

    err_arr = pred - exp
    mue = float(np.mean(np.abs(err_arr)))
    rmse = float(np.sqrt(np.mean(err_arr ** 2)))
    ss_tot = float(np.sum((exp - np.mean(exp)) ** 2))
    ss_res = float(np.sum(err_arr ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

    n = len(exp)
    conc = disc = 0
    for i in range(n):
        for j in range(i + 1, n):
            if (exp[i] - exp[j]) * (pred[i] - pred[j]) > 0: conc += 1
            elif (exp[i] - exp[j]) * (pred[i] - pred[j]) < 0: disc += 1
    tau = (conc - disc) / (n * (n - 1) / 2) if n > 1 else 0

    stats = f"N = {n}\nR\u00b2 = {r2:.3f}\nRMSE = {rmse:.2f} kcal/mol\nMUE = {mue:.2f} kcal/mol\nKendall \u03c4 = {tau:.3f}"
    ax.text(0.05, 0.95, stats, transform=ax.transAxes, fontsize=10, va="top",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow", edgecolor="gray"))

    ax.set_xlabel("Experimental \u0394\u0394G (kcal/mol)", fontsize=12)
    ax.set_ylabel("Predicted \u0394\u0394G (kcal/mol)", fontsize=12)
    ax.set_title("T4 Lysozyme L99A \u2014 FEP+ RBFE (ref: toluene)", fontsize=13)
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
    ax.set_aspect("equal"); ax.legend(loc="lower right", fontsize=9); ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(Path(out_dir) / "ddg_correlation.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("Saved: ddg_correlation.png")


def plot_edge_summary(edges, out_dir):
    fig, ax = plt.subplots(figsize=(10, 5))
    labels, ddgs, colors = [], [], []
    for e in edges:
        labels.append(f"{e['name1']} \u2192 {e['name2']}")
        cx = e["legs"].get("complex")
        sv = e["legs"].get("solvent")
        if cx and sv:
            ddgs.append(cx["dg"] - sv["dg"])
            colors.append("#4caf50" if e["completed"] else "#ff9800")
        else:
            ddgs.append(0); colors.append("#d32f2f")

    ax.bar(range(len(labels)), ddgs, color=colors, edgecolor="white", linewidth=0.5)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=9)
    ax.set_ylabel("\u0394\u0394G (complex \u2212 solvent) kcal/mol", fontsize=11)
    ax.set_title("Per-Edge FEP+ Results", fontsize=13)
    ax.axhline(y=0, color="gray", linestyle="-", linewidth=0.8)
    ax.grid(True, axis="y", alpha=0.3)

    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(facecolor="#4caf50", label="Completed"),
        Patch(facecolor="#ff9800", label="Partial"),
        Patch(facecolor="#d32f2f", label="Failed/Missing"),
    ], loc="upper right", fontsize=9)
    fig.tight_layout()
    fig.savefig(Path(out_dir) / "edge_summary.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("Saved: edge_summary.png")


def plot_leg_decomposition(edges, out_dir):
    labels, cx_dgs, sv_dgs, cx_errs, sv_errs = [], [], [], [], []
    for e in edges:
        labels.append(f"{e['name1']} \u2192 {e['name2']}")
        cx = e["legs"].get("complex")
        sv = e["legs"].get("solvent")
        cx_dgs.append(cx["dg"] if cx else 0); cx_errs.append(cx["err"] if cx else 0)
        sv_dgs.append(sv["dg"] if sv else 0); sv_errs.append(sv["err"] if sv else 0)

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(labels)); w = 0.35
    ax.bar(x - w / 2, cx_dgs, w, yerr=cx_errs, label="Complex", color="#1976d2", capsize=3, alpha=0.85)
    ax.bar(x + w / 2, sv_dgs, w, yerr=sv_errs, label="Solvent", color="#ff7043", capsize=3, alpha=0.85)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=9)
    ax.set_ylabel("\u0394G (kcal/mol)", fontsize=11)
    ax.set_title("Complex vs Solvent Leg \u0394G per Edge", fontsize=13)
    ax.legend(fontsize=10); ax.grid(True, axis="y", alpha=0.3); ax.axhline(y=0, color="gray", linewidth=0.8)
    fig.tight_layout()
    fig.savefig(Path(out_dir) / "leg_decomposition.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("Saved: leg_decomposition.png")


def write_qc_report(nodes, edges, out_dir):
    out = Path(out_dir) / "qc_report.txt"
    lines = [
        "=" * 70, "FEP+ RBFE QC Report — T4 Lysozyme L99A (181L)", "=" * 70, "",
        f"Reference ligand: {REF_LIGAND}", f"Ligands: {len(nodes)}", f"Edges: {len(edges)}",
        f"Completed: {sum(1 for e in edges if e['completed'])}/{len(edges)}", "",
        "--- Per-Ligand Results (ddG in kcal/mol, ref = toluene) ---",
        f"{'Ligand':<20s} {'Pred':>10s} {'Err':>8s} {'Exp':>10s} {'Diff':>10s}", "-" * 62,
    ]
    abs_errors = []
    for n in nodes:
        p, e_val, exp = n["pred_ddg"], n["pred_err"], n["exp_ddg"]
        if exp is not None:
            diff = p - exp; abs_errors.append(abs(diff))
            lines.append(f"  {n['name']:<18s} {p:>8.2f} {e_val:>8.2f} {exp:>8.2f} {diff:>10.2f}")
        else:
            lines.append(f"  {n['name']:<18s} {p:>8.2f} {e_val:>8.2f} {'N/A':>8s} {'N/A':>10s}")
    if abs_errors:
        mue = sum(abs_errors) / len(abs_errors)
        rmse = math.sqrt(sum(e ** 2 for e in abs_errors) / len(abs_errors))
        lines += ["", f"MUE  = {mue:.2f} kcal/mol", f"RMSE = {rmse:.2f} kcal/mol", f"N    = {len(abs_errors)}"]

    lines += ["", "--- Per-Edge Details ---",
              f"{'Edge':<35s} {'Complex dG':>12s} {'Solvent dG':>12s} {'ddG':>10s} {'Status':>10s}", "-" * 83]
    for e in edges:
        label = f"{e['name1']} -> {e['name2']}"
        cx = e["legs"].get("complex"); sv = e["legs"].get("solvent")
        cx_s = f"{cx['dg']:.4f}" if cx else "MISSING"
        sv_s = f"{sv['dg']:.4f}" if sv else "MISSING"
        ddg_s = f"{cx['dg'] - sv['dg']:.4f}" if cx and sv else "N/A"
        st = "OK" if e["completed"] else "INCOMPLETE"
        lines.append(f"  {label:<33s} {cx_s:>12s} {sv_s:>12s} {ddg_s:>10s} {st:>10s}")

    lines += ["", "--- QC Flags ---"]
    for e in edges:
        if not e["completed"]:
            lines.append(f"  WARNING: INCOMPLETE edge: {e['name1']} -> {e['name2']}")
            if not e["legs"].get("complex"):
                lines.append("    Missing: complex leg")
        if e["bad"]:
            lines.append(f"  BAD EDGE: {e['name1']} -> {e['name2']}")
    if abs_errors:
        if mue > 1.5: lines.append(f"  WARNING: MUE ({mue:.2f}) > 1.5 kcal/mol")
        if rmse > 2.0: lines.append(f"  WARNING: RMSE ({rmse:.2f}) > 2.0 kcal/mol")

    report = "\n".join(lines)
    out.write_text(report)
    print(f"Saved: {out}")
    print(); print(report)


def main():
    if len(sys.argv) < 3:
        print(f"Usage: $SCHRODINGER/run python3 {sys.argv[0]} <fmp_file> <output_dir>")
        sys.exit(1)
    fmp_path, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    print(f"Parsing {fmp_path}...")
    nodes, edges = parse_fmp(fmp_path)
    print(f"Found {len(nodes)} nodes, {len(edges)} edges\n")
    write_qc_report(nodes, edges, out_dir)
    plot_ddg_correlation(nodes, out_dir)
    plot_edge_summary(edges, out_dir)
    plot_leg_decomposition(edges, out_dir)
    print(f"\nAll QC outputs in: {out_dir}")


if __name__ == "__main__":
    main()
