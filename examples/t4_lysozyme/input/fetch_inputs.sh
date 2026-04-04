#!/usr/bin/env bash
# fetch_inputs.sh — Download PDB 181L (T4 lysozyme L99A + benzene) from RCSB.
#
# Usage:
#   cd examples/t4_lysozyme/input
#   bash fetch_inputs.sh
#
# Output:
#   181L.pdb — T4 lysozyme L99A crystal structure with benzene bound

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PDB_ID="181L"
PDB_FILE="${SCRIPT_DIR}/${PDB_ID}.pdb"

if [[ -f "$PDB_FILE" ]]; then
    echo "PDB file already exists: $PDB_FILE"
    exit 0
fi

echo "Downloading PDB ${PDB_ID} from RCSB..."
curl -fsSL "https://files.rcsb.org/download/${PDB_ID}.pdb" -o "$PDB_FILE"

if [[ -f "$PDB_FILE" ]]; then
    echo "Downloaded: $PDB_FILE"
    # Show basic info
    grep -c "^ATOM" "$PDB_FILE" | xargs -I{} echo "  Atoms: {}"
    grep "^HET " "$PDB_FILE" | head -5
else
    echo "ERROR: Download failed"
    exit 1
fi
