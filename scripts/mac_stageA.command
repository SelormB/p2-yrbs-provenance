#!/bin/bash
# Stage A on your Mac: Python env, CDC downloads (YRBS + BRFSS), data stages up to provenance.
# Double-click in Finder, or run: bash scripts/mac_stageA.command
# Everything stays inside this project folder. Log: logs/stageA.log
cd "$(dirname "$0")/.." || exit 1
mkdir -p logs
exec > >(tee -a logs/stageA.log) 2>&1
echo "=== Stage A start $(date) ==="
set -euo pipefail
PY=""
for c in "$HOME/anaconda3/bin/python" "$HOME/opt/anaconda3/bin/python" "/opt/anaconda3/bin/python" \
         "$HOME/miniconda3/bin/python" "/opt/homebrew/bin/python3" "/usr/local/bin/python3" "$(command -v python3 || true)"; do
  if [[ -n "$c" && -x "$c" ]] && "$c" -c 'import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)' 2>/dev/null; then PY="$c"; break; fi
done
[[ -z "$PY" ]] && { echo "No Python >= 3.10 found"; echo STAGEA_FAILED; exit 1; }
echo "Python: $PY ($("$PY" --version))"
[[ -d .venv ]] || "$PY" -m venv .venv
source .venv/bin/activate
python -m pip install -q --upgrade pip
python -m pip install -q -e ".[test]"
echo "--- download YRBS ---";  bash scripts/00_acquire.sh data/raw
echo "--- download BRFSS ---"; bash scripts/00_acquire_brfss.sh data/raw/brfss || echo "BRFSS download had errors (non-fatal)"
for st in resolve ingest audit provenance; do
  echo "--- stage $st $(date +%T) ---"
  python -m p2prov.cli $st --raw data/raw --out .
done
echo "STAGEA_DONE $(date)"
