# FEP QC Checklist

Quality control criteria for FEP+ calculations, based on Mey et al., "Best Practices for Alchemical Free Energy Calculations", *Living J. Comp. Mol. Sci.* 2020.

## Pre-Calculation Checks

- [ ] Protein structure is well-resolved (high resolution, no major missing regions)
- [ ] Protonation states match experimental assay pH
- [ ] Co-crystallized ligand pose is consistent with electron density
- [ ] Conserved binding site waters are retained
- [ ] Force field is appropriate for the system (OPLS4/OPLS5)
- [ ] Ligands have correct ionization states and tautomers

## RBFE-Specific Checks

- [ ] Ligands share a common scaffold (congeneric series)
- [ ] Each perturbation involves **≤ 5 heavy atoms**
- [ ] Perturbation network has cycle closure paths (not pure star map for production)
- [ ] No net charge changes between ligand pairs (or corrections applied)
- [ ] Atom mapping is chemically reasonable
- [ ] All binding poses are consistent and stable

## ABFE-Specific Checks

- [ ] Restraints are appropriate (Boresch/harmonic/flat-bottom)
- [ ] Standard state corrections are applied
- [ ] Ligand stays near binding site during decoupling
- [ ] Intramolecular interactions handled correctly

## Post-Calculation QC Metrics

### Statistical Uncertainty
- [ ] **σ ≤ 1 kcal/mol** for each perturbation
- [ ] Uncertainty is stable (not growing) with more sampling

### Overlap Matrix
- [ ] Off-diagonal elements **O_{i,i±1} ≥ 0.03** (minimum)
- [ ] Off-diagonal elements ~0.2 (good)
- [ ] No disconnected states in the overlap matrix
- [ ] If overlap is poor: **add λ windows** (more effective than longer simulations)

### Forward/Reverse Hysteresis
- [ ] Forward and reverse ΔG estimates agree within **1 kBT (~0.6 kcal/mol at 300K)**
- [ ] ΔG trajectory is stable in the second half of the simulation

### Estimator Consistency
- [ ] TI ≈ BAR ≈ MBAR (difference **< 1 kcal/mol**)
- [ ] If they disagree significantly: poor convergence

### Cycle Closure
- [ ] Closed thermodynamic cycles sum to **~0** kcal/mol
- [ ] Large cycle closure errors → extend poorly converging edges

### Energy Thresholds
- [ ] RBFE: No perturbation energy > **15 kcal/mol**
- [ ] ABFE: Binding energy > **−15 kcal/mol** (less negative is OK)

### Structural Checks
- [ ] Ligand RMSD is stable (ligand stays in binding site)
- [ ] Torsional sampling is adequate (multi-minima torsions sampled)
- [ ] Correlation time varies smoothly with λ
- [ ] ΔG changes smoothly with λ (no jumps)

## Overall Quality Assessment

| Metric | Good | Acceptable | Poor |
|--------|------|------------|------|
| MUE | < 1.0 kcal/mol | 1.0–1.5 kcal/mol | > 1.5 kcal/mol |
| RMSE | < 1.0 kcal/mol | 1.0–2.0 kcal/mol | > 2.0 kcal/mol |
| R² | > 0.7 | 0.3–0.7 | < 0.3 |
| Kendall τ | > 0.6 | 0.3–0.6 | < 0.3 |

## Recommended Reporting

When publishing or sharing FEP+ results, report:
- R², Kendall τ, MUE, RMSE
- Error bars via bootstrapping
- 1 and 2 kcal/mol confidence regions
- Number of replicates (≥ 3 recommended)
- Force field and simulation parameters
- Perturbation network topology
