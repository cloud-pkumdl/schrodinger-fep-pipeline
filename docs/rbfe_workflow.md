# RBFE Workflow

Relative Binding Free Energy (RBFE) using Schrödinger FEP+ computes **ΔΔG** between pairs of ligands in a congeneric series. This is the standard approach for lead optimization.

## Prerequisites

- Schrödinger Suite with FEP_GPGPU license
- NVIDIA GPU (RTX 3090/4090 recommended)
- Crystal structure with co-crystallized ligand
- Congeneric ligand series (SMILES or SDF)

## Step-by-Step

### 1. Protein Preparation (PrepWizard)

```bash
$SCHRODINGER/utilities/prepwizard \
    -fillloops -fillsidechains -rehtreat \
    -f OPLS4 -watdist 5.0 \
    input.pdb output_prepared.mae
```

Key operations:
- Assign bond orders
- Add hydrogens
- Fill missing loops and side chains
- Optimize H-bond network
- Restrained minimization (RMSD < 0.3 Å)

### 2. Ligand Preparation (LigPrep)

```bash
$SCHRODINGER/ligprep \
    -bff 14 -epik -ph 7.0 -pht 1.0 \
    -ifile ligands.smi -ofile ligands_prepared.maegz
```

Generates 3D coordinates, correct ionization states, and stereoisomers.

### 3. Docking (Glide SP)

```bash
# Generate receptor grid
$SCHRODINGER/glide grid.in -HOST localhost -WAIT

# Dock ligands
$SCHRODINGER/glide dock.in -HOST localhost -WAIT
```

Output: `*_pv.maegz` — poseviewer file containing protein + all docked poses.

### 4. FEP+ Perturbation Map

```bash
# Prepare only — generates map without MD
CUDA_VISIBLE_DEVICES=1 $SCHRODINGER/fep_plus \
    -HOST localhost -SUBHOST localhost \
    -JOBNAME fep_job -ff OPLS4 \
    -prepare docked_pv.maegz
```

**Always review the perturbation map before running MD.** Check:
- All ligands have reasonable poses
- Perturbations involve ≤ 5 heavy atoms per edge
- Network has cycle closure paths

### 5. FEP+ MD Simulation

```bash
CUDA_VISIBLE_DEVICES=1 $SCHRODINGER/fep_plus \
    -HOST localhost -SUBHOST localhost \
    -JOBNAME fep_job -ff OPLS4 -ppj 1 \
    docked_pv.maegz
```

Production settings:
- **sim_time**: 5000 ps (5 ns) per lambda window
- **lambda_windows**: 12
- **Time per edge**: ~2–12 hours on RTX 4090

Quick test settings:
- **sim_time**: 100 ps
- **lambda_windows**: 6

### 6. Analysis

The FMP file contains all results. Open in Maestro (FEP+ panel) or parse programmatically:

```python
from fep_pipeline.analysis import parse_fep_summary_csv, compute_qc_metrics

results = parse_fep_summary_csv("fep_job_summary.csv")
metrics = compute_qc_metrics(results)
```

## Perturbation Network Design

- **Star map**: Central ligand → all others. Fast but no cycle closure.
- **Connected network**: Redundant paths enable cycle closure error checking.
- **Max perturbation**: 1–5 heavy atoms per edge for reliable results.

## Common Issues

1. **Poor convergence**: Increase sim_time or lambda_windows
2. **Bad poses**: Re-dock with constraints or manual placement
3. **Charge changes**: Avoid net charge differences between ligand pairs
4. **Ring transformations**: May need intermediate scaffold
