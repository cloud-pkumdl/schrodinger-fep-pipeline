# T4 Lysozyme RBFE Results (Complete — All 6 Edges Converged)

## RBFE Run Summary
- **System**: T4 Lysozyme L99A (PDB: 181L)
- **Ligands**: 5 (benzene, toluene, ethylbenzene, p-xylene, chlorobenzene)
- **Edges**: 6
- **Force Field**: OPLS4
- **Lambda Windows**: 12 per edge
- **Sim Time**: 5000 ps per lambda window
- **GPU**: NVIDIA RTX 4090 (single GPU, GPU 0)
- **Total Duration**: ~9.5 hours (initial) + 5.5 min (restart for 1 failed edge)
- **Job Name**: t4l_fep_final

## Edge Results (kcal/mol)

| Edge | Complex dG | Solvent dG | Bennett ddG | Cycle Closure ddG |
|------|-----------|-----------|-------------|-------------------|
| ethylbenzene → toluene | -7.44±0.05 | -7.90±0.04 | 0.46±0.07 | 0.50±0.08 |
| ethylbenzene → p-xylene | -13.99±0.08 | -16.02±0.06 | 2.04±0.10 | 1.99±0.10 |
| toluene → chlorobenzene | 2.92±0.04 | 3.59±0.01 | -0.67±0.04 | -0.70±0.05 |
| toluene → benzene | 2.78±0.03 | 3.05±0.01 | -0.28±0.03 | -0.24±0.05 |
| toluene → p-xylene | -6.68±0.04 | -8.12±0.02 | 1.44±0.05 | 1.49±0.08 |
| chlorobenzene → benzene | -0.04±0.04 | -0.53±0.01 | 0.49±0.04 | 0.46±0.05 |

## Node (Ligand) Results — Relative Binding dG (kcal/mol)

| Ligand | Predicted ddG | Exp dG (kcal/mol) |
|--------|---------------|-------------------|
| toluene | 0.00±0.40 (ref) | -5.49 |
| ethylbenzene | -0.50±0.41 | -5.07 |
| chlorobenzene | -0.70±0.40 | -5.42 |
| benzene | -0.24±0.40 | -5.19 |
| p-xylene | 1.49±0.41 | -5.96 |

## Notes
- Initial Stage 4 had 1 failed subjob (toluene→chlorobenzene complex leg)
  due to CUDA illegal memory access from GPU contention (3 gdesmond on GPU 0)
- Restarted from checkpoint: only the failed edge reran (5.5 min)
- All results converged with low Bennett ddG uncertainty (<0.10 kcal/mol)
- Cycle closure ddG closely matches Bennett ddG (good self-consistency)
