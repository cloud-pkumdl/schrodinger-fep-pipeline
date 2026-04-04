# Multi-GPU Configuration for Schrödinger FEP+

## Overview

Schrödinger FEP+ (2025-4) assigns GPUs via the `schrodinger.hosts` file.
On a multi-GPU server, each `gpgpu:` entry defines an available GPU.

## Key Finding: Custom hosts file is IGNORED

In Schrödinger 2025-4, the user-level `~/.schrodinger/schrodinger.hosts` is
**ignored** with the warning:
```
WARNING The custom schrodinger.hosts file ... is being ignored.
```

This means you cannot restrict GPU usage by editing the user hosts file.

## Practical GPU Control Methods

### 1. CUDA_VISIBLE_DEVICES (Recommended)
Set before launching the FEP+ job:
```bash
CUDA_VISIBLE_DEVICES=0,3 $SCHRODINGER/fep_plus ...
```
This restricts CUDA to only see the specified GPUs.

### 2. System hosts file (Requires admin)
Edit `/opt/schrodinger2025-4/schrodinger.hosts` to only list free GPUs.
Requires root or schrodinger group membership.

### 3. -SUBHOST control
`-SUBHOST localhost:N` controls max concurrent subjobs.
Each subjob uses one GPU (with `-ppj 1`).
```bash
$SCHRODINGER/fep_plus -HOST localhost -SUBHOST localhost:2 -ppj 1 ...
```

## Multi-GPU FEP+ Distribution

FEP+ naturally distributes work across available GPUs:
- **RBFE**: Each edge has 2 legs (complex + solvent). With `-SUBHOST localhost:2`,
  both legs run simultaneously on different GPUs.
- **ABFE**: Similarly, complex and solvent FEP legs run in parallel.

### GPU Memory Usage
- Each gdesmond FEP+ process uses ~1.3-1.5 GB GPU memory
- A 49 GB RTX 4090 can easily run multiple FEP+ processes
- Main constraint is compute (100% GPU util per process), not memory

## Checking GPU Status
```bash
# Quick status
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader

# Show which processes use which GPU
nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory --format=csv,noheader

# Auto-select free GPUs (from common.sh)
source scripts/common.sh
zeus_pick_gpus 2 8000  # Pick 2 GPUs with >8GB free
```

## ABFE Limitations

### Benzene / Symmetric Ligands
ABFE fails for benzene and other highly symmetric ligands without
rotatable bonds:
```
WARNING: Could not find torsions to determine representative frame.
No interactions found.
Could not find cross link restraints using ligand interactions.
ERROR: Unable to find a suitable crosslink restraint.
```

The ABFE `fep_primer` stage requires torsional degrees of freedom
to set up crosslink restraints. Use toluene or larger ligands instead.
The `-ligand-restraint` flag does NOT fix this issue.
