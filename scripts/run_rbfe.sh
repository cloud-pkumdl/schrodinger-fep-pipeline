#!/usr/bin/env bash
# run_rbfe.sh — Full RBFE (Relative Binding Free Energy) pipeline.
#
# Runs the complete FEP+ RBFE workflow:
#   1. Prepare protein (PrepWizard)
#   2. Prepare ligands (LigPrep from SMILES)
#   3. Dock ligands (Glide SP)
#   4. Run FEP+ (generate perturbation map + MD)
#   5. Collect results
#
# Usage:
#   ./run_rbfe.sh <config.yaml>
#   ./run_rbfe.sh <config.yaml> --prepare     # Stop after FEP+ map generation
#   ./run_rbfe.sh <config.yaml> --gpu 2       # Use GPU 2
#
# Input:
#   config.yaml — Pipeline configuration (see examples/t4_lysozyme/config.yaml)
#
# Output:
#   <output_dir>/<job_name>.fmp — FEP+ results (open in Maestro)
#   <output_dir>/<job_name>_summary.csv — Per-ligand ΔΔG predictions

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

# ── Parse arguments ──────────────────────────────────────────────────

CONFIG_FILE=""
PREPARE_ONLY=false
GPU_OVERRIDE=""

usage() {
    cat <<EOF
Usage: $(basename "$0") <config.yaml> [options]

Options:
  --prepare       Only generate perturbation map, skip MD
  --gpu <id>      Override GPU ID from config
  -h, --help      Show this help

Examples:
  $(basename "$0") config.yaml                    # Full RBFE pipeline
  $(basename "$0") config.yaml --prepare          # Prepare only
  $(basename "$0") config.yaml --gpu 2            # Use GPU 2
EOF
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --prepare) PREPARE_ONLY=true; shift ;;
        --gpu) GPU_OVERRIDE="$2"; shift 2 ;;
        -h | --help) usage ;;
        -*) log_error "Unknown option: $1"; usage ;;
        *) CONFIG_FILE="$1"; shift ;;
    esac
done

[[ -z "$CONFIG_FILE" ]] && { log_error "Config file required"; usage; }
[[ -f "$CONFIG_FILE" ]] || { log_error "Config not found: $CONFIG_FILE"; exit 1; }

# ── Read config (basic YAML parsing) ────────────────────────────────

yaml_get() {
    # Simple single-value YAML extractor (no nested support)
    local key="$1" file="$2"
    grep -E "^${key}:" "$file" | head -1 | sed "s/^${key}:[[:space:]]*//" | tr -d '"' | tr -d "'"
}

JOB_NAME=$(yaml_get "job_name" "$CONFIG_FILE")
JOB_NAME="${JOB_NAME:-fep_rbfe}"
PROTEIN_FILE=$(yaml_get "protein_file" "$CONFIG_FILE")
LIGAND_FILE=$(yaml_get "ligand_file" "$CONFIG_FILE")
OUTPUT_DIR=$(yaml_get "output_dir" "$CONFIG_FILE")
OUTPUT_DIR="${OUTPUT_DIR:-output}"
GPU_ID="${GPU_OVERRIDE:-$(yaml_get "gpu_id" "$CONFIG_FILE")}"
GPU_ID="${GPU_ID:-1}"
FORCE_FIELD=$(yaml_get "force_field" "$CONFIG_FILE")
FORCE_FIELD="${FORCE_FIELD:-OPLS4}"
SIM_TIME=$(yaml_get "sim_time" "$CONFIG_FILE")
SIM_TIME="${SIM_TIME:-5000}"
LAMBDA_WINDOWS=$(yaml_get "lambda_windows" "$CONFIG_FILE")
LAMBDA_WINDOWS="${LAMBDA_WINDOWS:-12}"

mkdir -p "$OUTPUT_DIR"

log_info "=== RBFE Pipeline ==="
log_info "Job: $JOB_NAME | GPU: $GPU_ID | FF: $FORCE_FIELD"
log_info "Protein: $PROTEIN_FILE | Ligands: $LIGAND_FILE"
log_info "Sim: ${SIM_TIME}ps/λ × ${LAMBDA_WINDOWS}λ"

# ── Initialize remote ────────────────────────────────────────────────

log_info "Initializing remote server..."
zeus_init

# ── Step 1: Protein preparation ─────────────────────────────────────

PROT_BASE=$(basename "$PROTEIN_FILE" | sed 's/\.\(pdb\|mae\|maegz\)$//')
PREPARED_PROT="${PROT_BASE}_prepared.mae"

log_info "Step 1/5: Protein preparation (PrepWizard)"
zeus_upload "$PROTEIN_FILE" "$(basename "$PROTEIN_FILE")"

zeus "cd '$SCRATCH' && \
    $SCHRODINGER/utilities/prepwizard \
    -JOBNAME prep_${JOB_NAME} \
    -HOST localhost \
    -fillloops -fillsidechains -rehtreat \
    -f $FORCE_FIELD \
    -watdist 5.0 \
    '$(basename "$PROTEIN_FILE")' \
    '$PREPARED_PROT' 2>&1 | tail -5"

log_info "Protein preparation complete"

# ── Step 2: Ligand preparation ──────────────────────────────────────

LIGAND_BASE=$(basename "$LIGAND_FILE" | sed 's/\.\(smi\|sdf\|mae\|maegz\)$//')
PREPARED_LIGS="${LIGAND_BASE}_prepared.maegz"

log_info "Step 2/5: Ligand preparation (LigPrep)"
zeus_upload "$LIGAND_FILE" "$(basename "$LIGAND_FILE")"

zeus "cd '$SCRATCH' && \
    $SCHRODINGER/ligprep \
    -JOBNAME ligprep_${JOB_NAME} \
    -HOST localhost \
    -bff 14 -epik \
    -ifile '$(basename "$LIGAND_FILE")' \
    -ofile '$PREPARED_LIGS' 2>&1 | tail -5"

log_info "Ligand preparation complete"

# ── Step 3: Docking ─────────────────────────────────────────────────

GRID_JOB="${JOB_NAME}_grid"
DOCK_JOB="${JOB_NAME}_dock"
PV_FILE="${DOCK_JOB}_pv.maegz"

log_info "Step 3/5: Glide docking (SP)"

# Generate grid
zeus "cd '$SCRATCH' && cat > '${GRID_JOB}.in' <<GRIDINP
GRIDFILE   ${GRID_JOB}.zip
JOBNAME    ${GRID_JOB}
RECEP_FILE ${PREPARED_PROT}
GRID_CENTER SELF
INNERBOX   10.0,10.0,10.0
OUTERBOX   25.0,25.0,25.0
GRIDINP
$SCHRODINGER/glide '${GRID_JOB}.in' -HOST localhost -WAIT 2>&1 | tail -5"

# Dock ligands
zeus "cd '$SCRATCH' && cat > '${DOCK_JOB}.in' <<DOCKINP
JOBNAME      ${DOCK_JOB}
GRIDFILE     ${GRID_JOB}.zip
LIGANDFILE   ${PREPARED_LIGS}
PRECISION    SP
POSES_PER_LIG 1
POSTDOCK_NPOSE 1
DOCKINP
$SCHRODINGER/glide '${DOCK_JOB}.in' -HOST localhost -WAIT 2>&1 | tail -5"

log_info "Docking complete"

# ── Step 4: FEP+ ────────────────────────────────────────────────────

FEP_ARGS="-HOST localhost -SUBHOST localhost -JOBNAME $JOB_NAME -ff $FORCE_FIELD -ppj 1"

if $PREPARE_ONLY; then
    log_info "Step 4/5: FEP+ perturbation map (prepare only)"
    zeus "cd '$SCRATCH' && \
        CUDA_VISIBLE_DEVICES=$GPU_ID $SCHRODINGER/fep_plus $FEP_ARGS -prepare '$PV_FILE' 2>&1 | tail -10"
    log_info "Perturbation map generated. Open .fmp in Maestro to review."
else
    log_info "Step 4/5: FEP+ MD (${SIM_TIME}ps/λ × ${LAMBDA_WINDOWS}λ on GPU $GPU_ID)"
    log_warn "This is a long-running computation. Consider --prepare first."
    zeus "cd '$SCRATCH' && \
        CUDA_VISIBLE_DEVICES=$GPU_ID $SCHRODINGER/fep_plus $FEP_ARGS '$PV_FILE' 2>&1 | tail -20"
fi

log_info "FEP+ complete"

# ── Step 5: Collect results ──────────────────────────────────────────

log_info "Step 5/5: Collecting results"
zeus_download "$SCRATCH/${JOB_NAME}.fmp" "$OUTPUT_DIR/${JOB_NAME}.fmp" 2>/dev/null || true
zeus_download "$SCRATCH/${JOB_NAME}_summary.csv" "$OUTPUT_DIR/${JOB_NAME}_summary.csv" 2>/dev/null || true

log_info "=== RBFE Pipeline Complete ==="
log_info "Results: $OUTPUT_DIR/"
log_info "  FMP: ${JOB_NAME}.fmp (open in Maestro → FEP+ panel)"
log_info "  CSV: ${JOB_NAME}_summary.csv"
