#!/usr/bin/env bash
# Bundle aggregate outputs (no student-level rows) to share for the next build step.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="p2_results_$(date +%Y%m%d_%H%M).zip"
zip -qr "$OUT" results/audit results/metrics results/splits/manifest.json results/stats.json tables figures logs RUN_MODE.json \
  -x "results/preds/*" "data/*"
echo "$OUT"
