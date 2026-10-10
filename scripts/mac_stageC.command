#!/bin/bash
# Stage C on your Mac: BRFSS ACE testbed, then the full 1,000-replicate bootstrap for the two primary
# analyses (re-evaluation only; fitted predictions are reused). Log: logs/stageC.log
cd "$(dirname "$0")/.." || exit 1
exec > >(tee -a logs/stageC.log) 2>&1
echo "=== Stage C start $(date) ==="
set -uo pipefail
source .venv/bin/activate
echo "--- BRFSS $(date +%T) ---"
python -m p2prov.cli brfss --raw data/raw/brfss --out . --dev || echo "BRFSS FAILED"
for o in any_attempt injurious_attempt; do
  echo "--- full bootstrap $o S0_primary $(date +%T) ---"
  python -m p2prov.cli evaluate --outcome $o --scenario S0_primary --raw data/raw --out . || echo "EVAL FAILED $o"
done
python -m p2prov.cli report --raw data/raw --out .
echo "STAGEC_DONE $(date)"
