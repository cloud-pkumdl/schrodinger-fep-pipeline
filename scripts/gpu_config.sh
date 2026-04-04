#!/usr/bin/env bash
# gpu_config.sh — GPU management for Schrödinger FEP+ on multi-GPU servers.
#
# Schrödinger FEP+ assigns GPUs via schrodinger.hosts file (gpgpu entries).
# The user-level ~/.schrodinger/schrodinger.hosts is often IGNORED in
# Schrödinger 2025-4, so the practical approaches are:
#
#   1. Modify system hosts file (requires admin/schrodinger group)
#   2. Use CUDA_VISIBLE_DEVICES (works for most Desmond/gdesmond jobs)
#   3. Use -SUBHOST localhost:N to control max concurrent GPU jobs
#
# Usage:
#   source gpu_config.sh
#   configure_gpus "0,3"          # Only use GPUs 0 and 3
#   configure_gpus "auto"         # Auto-select free GPUs
#   configure_gpus "auto" 2       # Auto-select 2 free GPUs

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

configure_gpus() {
    local gpu_spec="${1:-auto}"
    local gpu_count="${2:-2}"

    if [[ "$gpu_spec" == "auto" ]]; then
        GPU_IDS=$(zeus_pick_gpus "$gpu_count" 8000)
        log_info "Auto-selected GPUs: $GPU_IDS"
    else
        GPU_IDS="$gpu_spec"
    fi

    export CUDA_VISIBLE_DEVICES="$GPU_IDS"
    GPU_COUNT=$(echo "$GPU_IDS" | tr ',' '
' | wc -l)
    export FEP_SUBHOST="localhost:${GPU_COUNT}"

    log_info "GPU config: CUDA_VISIBLE_DEVICES=$GPU_IDS, SUBHOST=$FEP_SUBHOST"
}

show_gpu_status() {
    log_info "GPU Status:"
    zeus_gpu_status
}
