# Pipeline Overview

## Architecture

```
                 ┌─────────────┐
                 │  PDB / SDF  │  Input structures
                 └──────┬──────┘
                        │
                 ┌──────▼──────┐
                 │  PrepWizard  │  Protein preparation
                 │  + LigPrep   │  Ligand preparation
                 └──────┬──────┘
                        │
                 ┌──────▼──────┐
                 │  Glide SP   │  Docking (pose generation)
                 └──────┬──────┘
                        │
              ┌─────────┴─────────┐
              │                   │
       ┌──────▼──────┐    ┌──────▼──────┐
       │   FEP+      │    │    ABFE     │
       │  (RBFE)     │    │  (Absolute) │
       │  ΔΔG_bind   │    │  ΔG_bind    │
       └──────┬──────┘    └──────┬──────┘
              │                   │
              └─────────┬─────────┘
                        │
                 ┌──────▼──────┐
                 │  Analysis   │  QC metrics, tables, plots
                 └─────────────┘
```

## Components

### Python Package (`src/fep_pipeline/`)

| Module | Purpose |
|--------|---------|
| `config.py` | YAML config loading with typed dataclasses |
| `protein_prep.py` | PrepWizard wrapper (H-bond opt, minimization) |
| `ligand_prep.py` | LigPrep wrapper (SMILES → 3D MAE) |
| `docking.py` | Glide grid generation + SP docking |
| `rbfe.py` | FEP+ relative binding free energy |
| `abfe.py` | Absolute binding free energy |
| `analysis.py` | Result parsing, QC metrics, reporting |
| `utils.py` | SSH/SCP helpers, logging, command execution |

### Shell Scripts (`scripts/`)

| Script | Purpose |
|--------|---------|
| `common.sh` | Shared functions: SSH, GPU management |
| `run_rbfe.sh` | End-to-end RBFE pipeline |
| `run_abfe.sh` | End-to-end ABFE pipeline |

## Execution Model

All Schrödinger computations run on a remote GPU server via SSH. The pipeline:

1. Uploads input files via SCP
2. Executes Schrödinger tools remotely
3. Downloads results back to the local machine

This design separates the orchestration (local) from the computation (remote GPU server), allowing the pipeline to be driven from any machine with SSH access.

## Configuration

All settings are in a single YAML file. See `examples/t4_lysozyme/config.yaml` for a complete example. Key sections:

- **server**: Remote host, Schrödinger path, working directories
- **prep**: Protein/ligand preparation parameters
- **docking**: Glide settings
- **fep**: RBFE simulation parameters
- **abfe**: ABFE simulation parameters
