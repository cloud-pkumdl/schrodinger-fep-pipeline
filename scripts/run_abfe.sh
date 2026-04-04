#!/usr/bin/env bash
# run_abfe.sh — Full ABFE (Absolute Binding Free Energy) pipeline.
#
# Runs the complete ABFE workflow:
#   1. Prepare input (protein-ligand complex from docking output or pv file)
#   2. Run fep_absolute_binding (complex leg + solvent leg)
#   3. Collect results
#
# Usage:
#   ./run_abfe.sh <config.yaml>
#   ./run_abfe.sh <config.yaml> --prepare     # Setup only, no MD
#   ./run_abfe.sh <config.yaml> --gpu 0,3     # Use GPUs 0 and 3
#
# Input:
#   config.yaml — Pipeline configuration with ABFE section
#
# Output:
#   <output_dir>/<job_name>-out.fmp — ABFE results (absolute binding ΔG)

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
  --prepare       Only prepare input, skip MD simulation
  --gpu <ids>     Override GPU IDs (e.g., "0,3" for GPUs 0 and 3)
  -h, --help      Show this help

Examples:
  $(basename "$0") config.yaml                    # Full ABFE
  $(basename "$0") config.yaml --prepare          # Prepare only
  $(basename "$0") config.yaml --gpu 0,3          # Multi-GPU
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

# ── Read config ──────────────────────────────────────────────────────

yaml_get() {
    local key="$1" file="$2"
    grep -E "^${key}:" "$file" | head -1 | sed "s/^${key}:[[:space:]]*//' | tr -d '"' | tr -d "'"
}

JOB_NAME=$(yaml_get "job_name" "$CONFIG_FILE")
JOB_NAME="${JOB_NAME:-abfe_job}"
COMPLEX_FILE=$(yaml_get "complex_file" "$CONFIG_FILE")
OUTPUT_DIR=$(yaml_get "output_dir" "$CONFIG_FILE")
OUTPUT_DIR="${OUTPUT_DIR:-output}"
FORCE_FIELD=$(yaml_get "force_field" "$CONFIG_FILE")
FORCE_FIELD="${FORCE_FIELD:-OPLS4}"
FEP_TIME=$(yaml_get "fep_sim_time" "$CONFIG_FILE")
FEP_TIME="${FEP_TIME:-5000}"
MD_TIME=$(yaml_get "md_sim_time" "$CONFIG_FILE")
MD_TIME="${MD_TIME:-1000}"

# GPU setup — use CUDA_VISIBLE_DEVICES since schrodinger.hosts custom
# files are ignored in Schrödinger 2025-4
GPUS="${GPU_OVERRIDE:-$(yaml_get "gpu_id" "$CONFIG_FILE")}"
GPUS="${GPUS:-0}"

if [[ "$GPUS" == *","* ]]; then
    GPU_COUNT=$(echo "$GPUS" | tr ',' '\n' | wc -l)
    SUBHOST="localhost:${GPU_COUNT}"
else
    SUBHOST="localhost:1"
fi

mkdir -p "$OUTPUT_DIR"

log_info "=== ABFE Pipeline ==="
log_info "Job: $JOB_NAME | GPU: $GPUS | FF: $FORCE_FIELD"
log_info "Complex: $COMPLEX_FILE"
log_info "FEP: ${FEP_TIME}ps | MD: ${MD_TIME}ps"

# ── Initialize ───────────────────────────────────────────────────────

zeus_init

# ── Upload complex ───────────────────────────────────────────────────

if [[ -z "$COMPLEX_FILE" ]]; then
    log_error "complex_file must be specified in config"
    exit 1
fi

COMPLEX_BASE=$(basename "$COMPLEX_FILE")
log_info "Uploading complex: $COMPLEX_BASE"
zeus_upload "$COMPLEX_FILE" "$COMPLEX_BASE"

# ── Run ABFE ─────────────────────────────────────────────────────────

# Build the command — note: -ppj controls GPUs per subjob (default: 4
# for multi-GPU parallelism within one edge; 1 for single-GPU).
# -SUBHOST localhost:N runs N subjobs concurrently across N GPUs.
ABFE_ARGS="-ff $FORCE_FIELD -fep-sim-time $FEP_TIME -md-sim-time $MD_TIME"
ABFE_ARGS="$ABFE_ARGS -HOST localhost -SUBHOST $SUBHOST -JOBNAME $JOB_NAME -ppj 1"

if $PREPARE_ONLY; then
    ABFE_ARGS="$ABFE_ARGS -prepare"
    log_info "Running ABFE in prepare-only mode"
else
    log_info "Running ABFE (FEP ${FEP_TIME}ps, MD ${MD_TIME}ps)"
    log_warn "ABFE is computationally expensive. Consider --prepare first."
fi

zeus "cd '$SCRATCH' && CUDA_VISIBLE_DEVICES=$GPUS $SCHRODINGER/fep_absolute_binding \
    '$SCRATCH/$COMPLEX_BASE' \
    $ABFE_ARGS 2>&1 | tail -20"

# ── Collect results ──────────────────────────────────────────────────

log_info "Collecting results..."
zeus_download "$SCRATCH/${JOB_NAME}-out.fmp" "$OUTPUT_DIR/${JOB_NAME}-out.fmp" 2>/dev/null || true
zeus_download "$SCRATCH/${JOB_NAME}.log" "$OUTPUT_DIR/${JOB_NAME}.log" 2>/dev/null || true

log_info "=== ABFE Pipeline Complete ==="
log_info "Results: $OUTPUT_DIR/"
log_info "  FMP: ${JOB_NAME}-out.fmp (open in Maestro -> FEP+ -> ABFE panel)"
log_info "  Absolute binding dG values are in the FMP file"
