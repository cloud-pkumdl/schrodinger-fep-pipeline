# ABFE Workflow

Absolute Binding Free Energy (ABFE) computes the absolute **ΔG_bind** for a single ligand. Unlike RBFE (which needs a congeneric series), ABFE works for individual compounds and can compare ligands with different scaffolds.

## When to Use ABFE

- Fragment screening (ranking diverse fragments)
- Cross-series compound comparison
- First active molecule evaluation
- Validating a binding mode

## Prerequisites

- Schrödinger Suite with FEP_GPGPU license
- Protein-ligand complex (from docking or crystal structure)
- NVIDIA GPU

## Thermodynamic Cycle

```
Protein·Ligand  ──(ΔG_complex)──>  Protein + Dummy
       │                                    │
  ΔG_bind                              ΔG = 0
       │                                    │
Protein + Ligand ──(ΔG_solvent)──>  Protein + Dummy(solv)

ΔG_bind = ΔG_complex - ΔG_solvent
```

Two simulation legs:
1. **Complex leg**: Ligand decoupled from protein binding site
2. **Solvent leg**: Ligand decoupled from solvent

## Step-by-Step

### 1. Prepare Complex

Start from a docked complex (poseviewer format MAE with protein first, ligand second):

```bash
# From RBFE docking output, extract a single complex
# Or use a crystal structure complex
```

### 2. Run ABFE (Prepare Only)

```bash
CUDA_VISIBLE_DEVICES=1 $SCHRODINGER/fep_absolute_binding \
    complex.mae \
    -ff OPLS4 \
    -fep-sim-time 1000 \
    -md-sim-time 200 \
    -HOST localhost \
    -SUBHOST localhost:1 \
    -JOBNAME abfe_test \
    -prepare
```

### 3. Run ABFE (Full)

```bash
CUDA_VISIBLE_DEVICES=1 $SCHRODINGER/fep_absolute_binding \
    complex.mae \
    -ff OPLS4 \
    -fep-sim-time 5000 \
    -md-sim-time 500 \
    -HOST localhost \
    -SUBHOST localhost:1 \
    -JOBNAME abfe_prod
```

Production: ~5000 ps FEP time, ~500 ps MD equilibration.

### 4. Multi-GPU Acceleration

```bash
CUDA_VISIBLE_DEVICES=1,2 $SCHRODINGER/fep_absolute_binding \
    complex.mae \
    -ff OPLS4 \
    -HOST localhost \
    -SUBHOST localhost:2 \
    -JOBNAME abfe_fast
```

### 5. Results

Output: `<jobname>-out.fmp` containing ΔG_bind.

Open in Maestro → FEP+ → ABFE panel, or parse the log for the binding free energy value.

## Key Considerations

- **Restraints**: ABFE uses Boresch restraints to keep the ligand near the binding site during decoupling. These are set automatically by Schrödinger.
- **Standard state correction**: Applied automatically.
- **Convergence**: ABFE typically needs longer simulations than RBFE.
- **Reliability threshold**: |ΔG_bind| > 15 kcal/mol suggests unreliable results.
- **Multiple binding modes**: If the ligand has multiple binding modes, consider running separate ABFE calculations for each.

## Comparison with RBFE

| Feature | RBFE | ABFE |
|---------|------|------|
| Output | Relative ΔΔG | Absolute ΔG_bind |
| Ligands needed | ≥ 2 (congeneric) | 1 |
| Cross-scaffold | No | Yes |
| Compute cost | Lower per edge | Higher per ligand |
| Accuracy | ~1 kcal/mol MUE | ~1–2 kcal/mol MUE |
| Best for | Lead optimization | Hit-to-lead, fragments |
