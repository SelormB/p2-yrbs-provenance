#!/bin/bash
#SBATCH --job-name=p2-prep
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --output=logs/slurm-%x-%j.out
# Data stages (serial). Submit from the repo root after `bash scripts/00_acquire.sh`.
# UNC cluster settings (partition/account/qos/module names) are site-specific: set them in slurm/site.env.
set -euo pipefail
[[ -f slurm/site.env ]] && source slurm/site.env
for st in resolve ingest audit provenance splits describe; do
  python -m p2prov.cli $st --raw data/raw --out .
done
