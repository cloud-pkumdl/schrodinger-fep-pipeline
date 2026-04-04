# FEP+ Parameter Guide

This document explains each pipeline parameter: what it controls, its default value, why that default was chosen, and when to change it.

## Simulation Parameters

### Lambda Windows

| Setting | Default | Range |
|---------|---------|-------|
| `fep.lambda_windows` | 12 | 11–24+ |

**What it controls:** The number of intermediate alchemical states between the physical end-states (λ=0 and λ=1). More windows means better overlap between adjacent states.

**Why 12:** Schrödinger's default for RBFE. Sufficient for small R-group changes involving 1–3 heavy atoms, which covers the majority of lead optimization perturbations. At 12 windows, adjacent MBAR overlap is typically ≥0.10 for these small changes.

**When to change:**
- **11 windows:** Schrödinger's minimal default. Fine for very conservative perturbations (single atom mutations, H→F, H→CH₃).
- **16–24 windows:** Use for larger perturbations (4–5 heavy atoms), scaffold hops, or any perturbation involving charge changes. The extra windows ensure adequate phase space overlap across the alchemical path.
- **24+ windows:** Ring transformations, fused ring changes, or any edge where MBAR overlap drops below 0.03. Adding windows is more effective than extending simulation time for fixing overlap issues (Mey et al. 2020).

### Simulation Time per Lambda Window

| Setting | Default | Range |
|---------|---------|-------|
| `fep.sim_time` | 5000 ps (5 ns) | 1000–20000 ps |

**What it controls:** The production MD simulation time at each lambda window. Longer simulations improve sampling and reduce statistical uncertainty.

**Why 5 ns:** Industry standard for production RBFE calculations. Based on extensive benchmarking by Schrödinger and academic groups (Wang et al. 2015, Mey et al. 2020). At 5 ns/λ with REST, most small-molecule perturbations in drug-like binding sites converge to ≤0.5 kcal/mol uncertainty.

**When to change:**
- **1 ns:** Quick validation runs only. Useful for checking that the setup is correct before committing GPU time.
- **10 ns:** Flexible binding sites, large perturbations, or when forward/reverse convergence shows a gap >0.5 kcal/mol at 5 ns.
- **20 ns:** Highly flexible systems, buried binding sites with slow water exchange, or membrane-bound targets where conformational sampling is limiting.

### Force Field

| Setting | Default | Options |
|---------|---------|---------|
| `fep.force_field` | OPLS4 | OPLS4, OPLS5 |

**What it controls:** The molecular mechanics force field used for all energy evaluations, including bonded terms, van der Waals, and electrostatics.

**Why OPLS4:** Schrödinger's current production force field, validated across thousands of FEP+ calculations in published benchmarks. OPLS4 has parameterization for >95% of drug-like chemical space and is the most extensively validated option for FEP+.

**When to change:**
- **OPLS5:** Available in Schrödinger 2025+. Improved torsional parameters and coverage of novel chemotypes. Use if working with unusual functional groups not well covered by OPLS4, but note that OPLS5 has less published FEP+ validation data.
- Never mix force fields within a single FEP+ campaign (perturbation network). All edges must use the same force field for thermodynamic consistency.

### Temperature

| Setting | Default | Range |
|---------|---------|-------|
| `fep.temperature` | 300.0 K | 298–310 K |

**What it controls:** The simulation temperature for production MD and free energy estimation.

**Why 300 K:** Standard approximation for room-temperature biochemical assays. Most experimental binding data is measured at 25°C (298 K) or 37°C (310 K). The difference between 298 K and 300 K is negligible for ΔΔG predictions (<0.02 kcal/mol effect).

**When to change:**
- **298 K:** If experimental data was measured precisely at 25°C and you need maximum rigor.
- **310 K:** For physiological temperature comparisons (cell-based assays at 37°C). Important for entropy-driven binders where TΔS contributions are significant.

## REST (Replica Exchange with Solute Tempering)

FEP+ uses REST by default to enhance conformational sampling in the binding site.

**What it does:** REST applies an effective elevated temperature (300–600 K) to the solute and nearby binding site residues, while keeping the bulk solvent at 300 K. This accelerates barrier crossing for:
- Ligand torsional rotations
- Side chain flips in the binding site
- Local water rearrangement

**Why it matters:** Without REST, FEP+ simulations at 5 ns/λ would frequently get trapped in local minima, especially for ligands with rotatable bonds in confined binding sites. REST is one of the key technological advantages of Schrödinger's FEP+ over basic alchemical methods.

**Parameters (set automatically by FEP+):**
- Hot region: ligand + residues within 5 Å of ligand
- Effective temperature range: 300–600 K
- Number of REST replicas: same as lambda windows

## Perturbation Map

### Maximum Common Substructure (MCS) Atom Mapping

**What it controls:** How atoms are mapped between ligand pairs for alchemical transformations. FEP+ uses an MCS-based algorithm (similar to LOMAP) to identify the largest common substructure and define which atoms appear/disappear.

**Best practices:**
- Each edge should involve **≤5 heavy atom changes**. Beyond this, overlap degrades and convergence becomes unreliable.
- The perturbation graph should be **well-connected** (no isolated subgraphs). Star maps (one reference ligand connected to all others) are simple but have no cycle closure. Use a connected graph with redundant edges for production.
- Always review the atom mapping visually before running MD. Incorrect mappings are the most common source of FEP+ failures.

### Network Topology

| Topology | Pros | Cons | Use when |
|----------|------|------|----------|
| Star | Simple, few edges | No cycle closure, error propagation | Quick screening |
| Pairwise | Redundant, cycle closure | Many edges, expensive | Production |
| LOMAP-optimized | Balanced | Requires LOMAP | Default for FEP+ |

## ABFE-Specific Parameters

### FEP Simulation Time (ABFE)

| Setting | Default | Range |
|---------|---------|-------|
| `abfe.fep_sim_time` | 5000 ps | 5000–20000 ps |

**What it controls:** Production simulation time for the alchemical decoupling legs (complex and solvent).

**Why 5 ns:** Same rationale as RBFE. ABFE convergence is generally harder than RBFE, so 5 ns is a starting point. Extend to 10–20 ns if convergence plots show instability.

### MD Equilibration Time (ABFE)

| Setting | Default | Range |
|---------|---------|-------|
| `abfe.md_sim_time` | 500 ps | 500–2000 ps |

**What it controls:** Pre-FEP equilibration MD to relax the system before alchemical transformations begin.

**Why 500 ps:** Sufficient for most pre-equilibrated systems. The protein was already minimized and equilibrated during preparation.

**When to change:**
- **2000 ps:** If starting from a homology model or significantly modified structure.
- **500 ps is usually fine:** If the structure came from X-ray crystallography and was prepared with PrepWizard.

## GPU Configuration

### GPU Selection

| Setting | Default | Notes |
|---------|---------|-------|
| `fep.gpu_id` | 0 | Single GPU ID |
| `abfe.gpu_ids` | [0] | List of GPU IDs |

**What it controls:** Which GPU(s) to use for MD simulations.

**Best practices:**
- **1 GPU per edge** is standard for RBFE. Each perturbation edge runs independently.
- Check GPU availability with `nvidia-smi` before launching. Use whichever GPU has the least memory usage.
- For ABFE with multiple ligands, distribute across GPUs: each ligand's complex and solvent legs can run on separate GPUs.
- FEP+ uses CUDA. Ensure the GPU driver is compatible with the Schrödinger release.

## Protein Preparation

### PrepWizard Parameters

| Setting | Default | Why |
|---------|---------|-----|
| `prep.fill_loops` | true | Missing loops near the binding site alter pocket shape |
| `prep.fill_side_chains` | true | Missing side chains cause steric artifacts |
| `prep.water_dist` | 5.0 Å | Remove waters >5 Å from het groups; binding site waters retained |
| `prep.target_ph` | 7.0 | Standard assay pH; adjust for acidic/basic assay conditions |

## Docking Parameters

### Glide Settings

| Setting | Default | Why |
|---------|---------|-----|
| `docking.precision` | SP | Standard Precision balances speed and accuracy for pose generation |
| `docking.poses_per_lig` | 1 | FEP+ needs one representative pose per ligand |

**When to use XP (Extra Precision):** When SP poses look questionable or when working with very flexible ligands that need more rigorous scoring.

## References

- Mey, A.S.J.S. et al. "Best Practices for Alchemical Free Energy Calculations: Article v1.0." *Living J. Comp. Mol. Sci.* 2(1), 18378 (2020).
- Wang, L. et al. "Accurate and Reliable Prediction of Relative Ligand Binding Potency in Prospective Drug Discovery by Way of a Modern Free-Energy Calculation Protocol and Force Field." *JACS* 137(7), 2695–2703 (2015).
- Cournia, Z. et al. "Relative Binding Free Energy Calculations in Drug Discovery: Recent Advances and Practical Considerations." *J. Chem. Inf. Model.* 57(12), 2911–2937 (2017).
