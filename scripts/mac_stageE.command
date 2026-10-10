#!/bin/bash
# Stage E: re-evaluate all tasks with survey-level variance strata (fits reused from checkpoints).
# Sensitivity scenarios: 200 replicates. Primary (S0) for both outcomes: 1,000 replicates. Log: logs/stageE.log
cd "$(dirname "$0")/.." || exit 1
exec > >(tee -a logs/stageE.log) 2>&1
echo "=== Stage E start $(date) ==="
source .venv/bin/activate
for i in $(seq 0 25); do
  read o s <<< "$(python -m p2prov.cli list-tasks | awk -v i=$i '$1==i{print $2, $3}')"
  if [[ "$s" == "S0_primary" ]]; then R=""; else R="--dev"; fi
  python -m p2prov.cli evaluate --outcome $o --scenario $s --raw data/raw --out . $R > logs/tasks/eval_$i.log 2>&1 && echo "eval $i $o $s ok $(date +%T)" || echo "eval $i FAILED $(date +%T)"
done
python -m p2prov.cli report --raw data/raw --out .
echo "STAGEE_DONE $(date)"
