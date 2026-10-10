#!/bin/bash
# Stage B on your Mac: re-run data stages with fixes, splits, prevalence, then all 26 tasks in parallel
# with 50 bootstrap replicates (preliminary CIs), then figures/tables. Log: logs/stageB.log
cd "$(dirname "$0")/.." || exit 1
mkdir -p logs/tasks
exec > >(tee -a logs/stageB.log) 2>&1
echo "=== Stage B start $(date) ==="
echo "cpu=$(sysctl -n hw.ncpu) mem_gb=$(( $(sysctl -n hw.memsize) / 1073741824 ))"
set -uo pipefail
source .venv/bin/activate
python -m pip install -q -e ".[test]"
python -m pytest -q || { echo STAGEB_FAILED tests; exit 1; }
for st in resolve ingest audit provenance splits describe; do
  echo "--- stage $st $(date +%T) ---"
  python -m p2prov.cli $st --raw data/raw --out . || { echo "STAGEB_FAILED $st"; exit 1; }
done
NCPU=$(sysctl -n hw.ncpu); MEMGB=$(( $(sysctl -n hw.memsize) / 1073741824 ))
P=$(( NCPU / 3 )); M=$(( MEMGB / 5 )); (( M < P )) && P=$M; (( P < 1 )) && P=1
export OMP_NUM_THREADS=3
echo "--- 26 tasks, $P in parallel, $(date +%T) ---"
seq 0 25 | xargs -P "$P" -I{} sh -c 'python -m p2prov.cli task --task-id {} --raw data/raw --out . --dev > logs/tasks/task_{}.log 2>&1 && echo "task {} ok $(date +%T)" || echo "task {} FAILED $(date +%T)"'
echo "--- report $(date +%T) ---"
python -m p2prov.cli report --raw data/raw --out . --dev
echo "STAGEB_DONE $(date)"
