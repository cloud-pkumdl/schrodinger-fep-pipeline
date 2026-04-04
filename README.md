# Schrödinger FEP+ Pipeline

A production-quality wrapper for running Schrödinger FEP+ (RBFE and ABFE) free energy calculations.

## Overview

This repository provides a clean, scriptable interface to the Schrödinger FEP+ workflow:

- **RBFE** (Relative Binding Free Energy): Compare binding affinities across a congeneric ligand series
- **ABFE** (Absolute Binding Free Energy): Compute absolute ΔG_bind for individual ligands

The pipeline handles protein preparation, ligand preparation, docking, FEP+ setup, execution, and result analysis.

## Requirements

- **Schrödinger Suite 2025-4** (or compatible version) with FEP_GPGPU license
- **Python 3.10+**
- **NVIDIA GPU** (RTX 3090/4090 recommended)

## Quick Start

```bash
# Clone
git clone https://github.com/cloud-pkumdl/schrodinger-fep-pipeline.git
cd schrodinger-fep-pipeline

# Install Python package (editable)
pip install -e .

# Run the T4 lysozyme example
cd examples/t4_lysozyme
bash input/fetch_inputs.sh
bash ../../scripts/run_rbfe.sh config.yaml
```

## Project Structure

```
src/fep_pipeline/       Python package (config, prep, docking, FEP+, analysis)
scripts/                Shell entry points for full pipelines
examples/t4_lysozyme/   Worked example with T4 lysozyme L99A
tests/                  Unit tests (run without Schrödinger)
docs/                   Pipeline documentation and QC checklists
```

## T4 Lysozyme Example

PDB [181L](https://www.rcsb.org/structure/181L) — T4 lysozyme L99A mutant with benzene bound.
A classic benchmark system for FEP+ validation with well-characterized congeneric binders:

| Ligand         | Experimental ΔG (kcal/mol) |
|----------------|---------------------------|
| Benzene        | −5.19                     |
| Toluene        | −5.49                     |
| Ethylbenzene   | −5.07                     |
| p-Xylene       | −5.96                     |
| Chlorobenzene  | −5.42                     |
| Phenol         | −4.73                     |

Source: Morton et al., *Biochemistry* 1995; Mobley et al., *J. Mol. Biol.* 2007.

## Pipeline Steps

### RBFE Workflow

1. **Protein preparation** — PrepWizard (H-bond optimization, restrained minimization)
2. **Ligand preparation** — LigPrep (3D coordinates, ionization states)
3. **Docking** — Glide SP (pose generation)
4. **FEP+ setup** — Generate perturbation map, validate network
5. **FEP+ MD** — GPU-accelerated free energy simulations
6. **Analysis** — Parse results, QC metrics (overlap, hysteresis, cycle closure)

### ABFE Workflow

1. **Complex preparation** — Protein-ligand complex from docking
2. **ABFE setup** — `fep_absolute_binding` with restraints
3. **Analysis** — Extract absolute ΔG_bind

See [docs/](docs/) for detailed workflow documentation.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/
ruff format --check src/ tests/

# Shell script checks
shellcheck scripts/*.sh
```

## License

[MIT](LICENSE)
