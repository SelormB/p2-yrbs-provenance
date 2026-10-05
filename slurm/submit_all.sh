#!/usr/bin/env bash
# Chain: prep -> 26-task array -> report. Usage (repo root, login node): bash slurm/submit_all.sh
set -euo pipefail
N=$(python -m p2prov.cli list-tasks | wc -l); LAST=$((N-1))
J0=$(sbatch --parsable slurm/00_prep.sbatch)
J1=$(sbatch --parsable --dependency=afterok:$J0 --array=0-${LAST}%10 slurm/01_tasks.sbatch)
J2=$(sbatch --parsable --dependency=afterany:$J1 slurm/02_report.sbatch)
echo "prep=$J0 tasks=$J1 report=$J2"
