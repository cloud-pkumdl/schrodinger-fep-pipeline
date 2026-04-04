# T4 Lysozyme L99A — FEP+ Worked Example

## System

**PDB: [181L](https://www.rcsb.org/structure/181L)** — T4 lysozyme L99A mutant with benzene bound in the hydrophobic cavity. This is the standard benchmark system for FEP+ validation.

The L99A mutation creates an apolar cavity (~150 Å³) that binds small hydrophobic molecules. Experimental binding data is well-characterized, making it ideal for FEP+ method validation.

## Ligand Series

| Ligand | SMILES | Exp ΔG (kcal/mol) |
|--------|--------|-------------------|
| Benzene | `c1ccccc1` | −5.19 |
| Toluene | `Cc1ccccc1` | −5.49 |
| Ethylbenzene | `CCc1ccccc1` | −5.07 |
| p-Xylene | `Cc1ccc(C)cc1` | −5.96 |
| Chlorobenzene | `Clc1ccccc1` | −5.42 |
| Phenol | `Oc1ccccc1` | −4.73 |
| Propylbenzene | `CCCc1ccccc1` | −4.62 |
| Fluorobenzene | `Fc1ccccc1` | −4.68 |
| Iodobenzene | `Ic1ccccc1` | −5.46 |
| Pyridine | `c1ccncc1` | −3.88 |

Sources: Morton et al., *Biochemistry* 1995; Mobley et al., *J. Mol. Biol.* 2007.

## Quick Start

### 1. Fetch input structure

```bash
cd examples/t4_lysozyme
bash input/fetch_inputs.sh
```

### 2. Run RBFE pipeline (prepare only)

```bash
# Generates perturbation map without running MD
../../scripts/run_rbfe.sh config.yaml --prepare
```

### 3. Run full RBFE (production)

```bash
# Full FEP+ run (5ns/λ × 12λ — takes hours per edge on RTX 4090)
../../scripts/run_rbfe.sh config.yaml
```

### 4. Quick test run

Edit `config.yaml` to set short simulation parameters:

```yaml
fep:
  sim_time: 100        # 100 ps instead of 5000 ps
  lambda_windows: 6    # 6 windows instead of 12
```

Then run:
```bash
../../scripts/run_rbfe.sh config.yaml
```

### 5. ABFE (single ligand)

For absolute binding free energy of benzene:

```bash
# Requires a docked complex MAE file
../../scripts/run_abfe.sh config.yaml --prepare
```

## Expected Results

For this well-studied system with OPLS4, expect:
- **MUE**: ~0.5–1.0 kcal/mol
- **R²**: > 0.5
- **RMSE**: < 1.5 kcal/mol

## File Structure

```
t4_lysozyme/
├── README.md           # This file
├── config.yaml         # Pipeline configuration
├── input/
│   ├── fetch_inputs.sh # Downloads PDB 181L
│   ├── ligands.smi     # Ligand SMILES + experimental data
│   └── 181L.pdb        # (downloaded by fetch_inputs.sh)
└── output/             # Results (git-ignored)
```
