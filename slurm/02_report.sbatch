#!/bin/bash
#SBATCH --job-name=p2-report
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --output=logs/slurm-%x-%j.out
set -euo pipefail
[[ -f slurm/site.env ]] && source slurm/site.env
python -m p2prov.cli report --raw data/raw --out .
bash scripts/pack_results.sh
