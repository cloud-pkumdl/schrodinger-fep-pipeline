# ABFE Toluene → T4 Lysozyme Results

**Date:** 2026-04-05
**Job ID:** 69a66930-3066-11f1-9683-3e2c17fa2259
**Duration:** 6h 15m 30s (04:39 → 10:55)
**Host:** Zeus (cloud@100.71.111.116)

## Absolute Binding Free Energy

| Compound | Complex dG (kcal/mol) | Solvent dG (kcal/mol) | Bennett Binding ddG (kcal/mol) | Boresch Corr. (kcal/mol) |
|----------|----------------------|----------------------|------------------------------|--------------------------|
| toluene  | 7.28 ± 0.03         | -6.80 ± 0.04        | **-4.47 ± 0.05**            | -9.61                    |

### Final Result

**ΔG_bind (toluene → 181L) = -4.47 ± 0.05 kcal/mol**

The Bennett ratio method gives the absolute binding free energy. The Boresch restraint correction of -9.61 kcal/mol was applied to the complex leg during simulation.

## FEP Stages

- Stage 1: task (0s)
- Stage 2: forcefield_builder (skipped)
- Stage 3: fep_absolute_binding_md_launcher (4m 46s)
- Stage 4: fep_absolute_binding_fep_launcher (6h 10m 34s)
  - Solvent sub-job: 3h 19m 52s
  - Complex sub-job: 6h 10m 20s
- Stage 5: fep_absolute_binding_analysis (9s)

## Output Files

- `t4l_abfe_toluene_out.fmp` — FEP map file with results
- `t4l_abfe_toluene_out.fmpdb` — FEP database file
- `t4l_abfe_toluene_multisim.log` — Full multisim log

## Workflow Parameters

- OPLS4 force field
- FEP sim time: 5000 ps per lambda window
- MD sim time: 1000 ps
- vdW perturbation: 60 lambda windows
- Charge perturbation: 60 lambda windows
- Restraint perturbation: 68 lambda windows
- Lambda hopping: 5 ns REMD
