#!/bin/bash
# Stage D: re-run the one task that failed in Stage B (task 16), after Stage C finishes; then rebuild report.
cd "$(dirname "$0")/.." || exit 1
exec > >(tee -a logs/stageD.log) 2>&1
source .venv/bin/activate
until grep -q STAGEC_DONE logs/stageC.log; do echo "waiting for Stage C... $(date +%T)"; sleep 120; done
python -m p2prov.cli task --task-id 16 --raw data/raw --out . --dev && echo "task 16 ok"
python -m p2prov.cli report --raw data/raw --out .
echo "STAGED_DONE $(date)"
