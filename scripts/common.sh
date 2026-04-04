#!/usr/bin/env bash
# common.sh — Shared configuration: SSH, Schrödinger environment, GPU management.
# Source this in pipeline shell scripts.
#
# Provides:
#   - zeus()           — Run command on remote compute server
#   - zeus_init()      — Ensure remote directories exist
#   - zeus_upload()    — Upload file to remote scratch
#   - zeus_download()  — Download file from remote
#   - zeus_pick_gpu()  — Auto-select best available GPU
#   - zeus_gpu_status() — Show GPU utilization

set -euo pipefail

# ── Server configuration ─────────────────────────────────────────────
ZEUS_HOST="${ZEUS_HOST:-cloud@100.71.111.116}"
SCHRODINGER="${SCHRODINGER:-/opt/schrodinger2025-4}"
REMOTE_WORKDIR="${REMOTE_WORKDIR:-/data2/cloud/schrodinger-skills}"
SCRATCH="${SCRATCH:-/scratch/cloud-fep-pipeline}"

# ── Remote execution ─────────────────────────────────────────────────

zeus() {
    # Execute a command on the remote server via SSH
    ssh "$ZEUS_HOST" "$@"
}

zeus_init() {
    # Ensure remote working directories exist
    zeus "mkdir -p '$REMOTE_WORKDIR' '$SCRATCH'"
}

zeus_upload() {
    # Upload a local file to the remote scratch directory
    # Usage: zeus_upload <local_file> [remote_name]
    local local_file="$1"
    local remote_name="${2:-$(basename "$local_file")}"
    scp "$local_file" "${ZEUS_HOST}:${SCRATCH}/${remote_name}"
    echo "${SCRATCH}/${remote_name}"
}

zeus_download() {
    # Download a file from the remote server
    # Usage: zeus_download <remote_path> [local_dest]
    local remote_file="$1"
    local local_dest="${2:-.}"
    scp "${ZEUS_HOST}:${remote_file}" "$local_dest"
}

# ── GPU management ───────────────────────────────────────────────────

zeus_gpu_status() {
    # Show GPU utilization on the remote server
    zeus "nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu \
          --format=csv,noheader"
}

zeus_pick_gpu() {
    # Auto-select the GPU with most free memory
    # Usage: zeus_pick_gpu [min_memory_mib]
    local need_mem="${1:-8000}"
    zeus "python3 -c \"
import subprocess, sys
result = subprocess.run(
    ['nvidia-smi', '--query-gpu=index,memory.used,memory.total',
     '--format=csv,noheader,nounits'],
    capture_output=True, text=True)
gpus = []
for line in result.stdout.strip().split('\n'):
    parts = [x.strip() for x in line.split(',')]
    idx, used, total = int(parts[0]), int(parts[1]), int(parts[2])
    gpus.append((idx, used, total - used))
gpus.sort(key=lambda g: -g[2])  # most free memory first
need = int(sys.argv[1])
for g in gpus:
    if g[2] >= need:
        print(g[0])
        sys.exit(0)
print(gpus[0][0])
\" \"$need_mem\""
}

zeus_pick_gpus() {
    # Select multiple GPUs with most free memory
    # Usage: zeus_pick_gpus <count> [min_memory_mib]
    local count="${1:-1}"
    local need_mem="${2:-8000}"
    zeus "python3 -c \"
import subprocess, sys
result = subprocess.run(
    ['nvidia-smi', '--query-gpu=index,memory.used,memory.total',
     '--format=csv,noheader,nounits'],
    capture_output=True, text=True)
gpus = []
for line in result.stdout.strip().split('\n'):
    parts = [x.strip() for x in line.split(',')]
    idx, used, total = int(parts[0]), int(parts[1]), int(parts[2])
    gpus.append((idx, used, total - used))
gpus.sort(key=lambda g: -g[2])
need = int(sys.argv[1])
count = int(sys.argv[2])
selected = []
for g in gpus:
    if g[2] >= need and len(selected) < count:
        selected.append(str(g[0]))
if len(selected) < count:
    for g in gpus:
        if str(g[0]) not in selected and len(selected) < count:
            selected.append(str(g[0]))
print(','.join(selected))
\" \"$need_mem\" \"$count\""
}

# ── Logging helpers ──────────────────────────────────────────────────

log_info() {
    echo "[$(date '+%H:%M:%S')] INFO: $*"
}

log_warn() {
    echo "[$(date '+%H:%M:%S')] WARN: $*" >&2
}

log_error() {
    echo "[$(date '+%H:%M:%S')] ERROR: $*" >&2
}
