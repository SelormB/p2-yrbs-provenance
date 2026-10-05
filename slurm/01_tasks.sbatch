#!/bin/bash
#SBATCH --job-name=p2-task
#SBATCH --array=0-25%10
#SBATCH --time=12:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --output=logs/slurm-%x-%A_%a.out
# One (outcome, scenario) per array index; `python -m p2prov.cli list-tasks` prints the map.
# Checkpointed: a task whose predictions exist skips refitting and only re-evaluates.
set -euo pipefail
[[ -f slurm/site.env ]] && source slurm/site.env
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
python -m p2prov.cli task --task-id "${SLURM_ARRAY_TASK_ID}" --raw data/raw --out .
