#!/usr/bin/env bash
# One-command real-data run on the MacBook: acquire -> data stages -> all tasks (dev bootstrap) -> report.
# Usage: bash scripts/run_local.sh [--full]    (--full uses 1000 bootstrap reps; slow on a laptop)
set -euo pipefail
cd "$(dirname "$0")/.."
DEV="--dev"; [[ "${1:-}" == "--full" ]] && DEV=""
bash scripts/00_acquire.sh data/raw
python -m p2prov.cli all --raw data/raw --out . $DEV
python -m pytest -q
echo "Finished. Send: results/ tables/ figures/ logs/ (zip with: bash scripts/pack_results.sh)"
