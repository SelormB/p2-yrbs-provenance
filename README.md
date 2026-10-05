# Project 2 — Missingness provenance in youth suicide-attempt prediction (YRBS)

DRAFT — UNVERIFIED. Nothing here is a published result. Outputs from synthetic test fixtures are stamped **SYNTHETIC — NOT A SCIENTIFIC RESULT**.

## What this is

In the CDC Youth Risk Behavior Survey combined data, a blank answer can mean several different things:
- the site did not ask the question;
- the question was not on that year's questionnaire;
- the student skipped it; or
- CDC edited an inconsistent answer to missing.

This project labels each blank by its identifiable source (`docs/taxonomy.md`). It then tests whether handling those sources differently changes prediction of past-year suicide attempt and injurious suicide attempt, and whether any gain is just the model learning which survey a student came from.

**Author:** Selorm Buaka, University of Northern Colorado. Co-authors: PLACEHOLDER.

## Quick start — MacBook (real data)

```bash
git clone <repo> && cd p2-yrbs-provenance
conda env create -f environment.yml && conda activate p2prov   # or: pip install -e ".[test]"
bash scripts/run_local.sh          # download CDC files, run every stage with dev bootstrap, run tests
bash scripts/pack_results.sh       # zip aggregate outputs (no student-level rows) to share
```

## Quick start — UNC HPC (Slurm)

```bash
cp slurm/site.env.example slurm/site.env   # add account/partition/module lines
bash scripts/00_acquire.sh data/raw         # on a login node with internet
bash slurm/submit_all.sh                    # prep -> 26-task array (checkpointed) -> report + zip
```

## Stages

Each stage reads and writes files only, so stages can be rerun one at a time.

| Script | Stage | Main outputs |
|---|---|---|
| `00_acquire.sh` | Download CDC files + checksums | `data/raw/`, `SHA256SUMS.txt` |
| `01_resolve_variables.py` | Map predictor concepts to CDC QN variables by label | `results/audit/variable_map.csv` |
| `02_ingest.py` | Read fixed-width files using CDC's own SAS layout | `data/interim/yrbs_raw.parquet`, `results/audit/data_provenance.csv` |
| `03_audit_years.py` | Apply the year-window rules | `results/audit/window.json`, `tables/T_audit_years.csv` |
| `04_provenance.py` | Provenance code for every cell | `data/processed/provenance.parquet`, `tables/T_provenance_*.csv`, `T_skip_consistency.csv`, `T_outcome_pair_missingness.csv` |
| `05_splits.py` | Frozen, hashed splits | `results/splits/*.parquet`, `manifest.json` |
| `06_describe.py` | Design-based prevalence, cohort flow | `tables/T_prevalence.csv`, `T_flow__*.csv` |
| `07_fit_task.py --task-id N` | Fit all methods and evaluate one (outcome, scenario) pair | `results/preds/`, `results/metrics/` |
| `08_report.py` | Figures, tables, `stats.json` | `figures/F1–F4`, `tables/T2–T4`, `results/stats.json` |

`python -m p2prov.cli list-tasks` prints the 26 (outcome, scenario) pairs.

## Testing without CDC data

```bash
python -m pytest -q        # unit tests + end-to-end run on synthetic fixtures
```

## Key documents

- `docs/source_audit.md`
- `docs/taxonomy.md`
- `docs/protocol.md`
- `docs/literature_review.md`
- `docs/variable_dictionary.md`
- `docs/DECISIONS.md`
- `docs/VERIFICATION.md`
- `STATUS.md`
- `manuscript/`
- `cste/TRACKER.md`

## Reproducibility

- **Seeds.** All randomness flows from `project.seed` in `config/project.yaml`.
- **Splits.** Splits are frozen with SHA-256. A changed split is refused.
- **Data checksums.** Raw files are checksummed at acquisition and again at ingest.
- **Numbers in text.** Every number in the manuscript comes from `results/stats.json` via `manuscript/render.py`. The renderer refuses synthetic statistics.

## License

- Code: MIT.
- Documentation and aggregate results: CC BY 4.0 (provisional).
- YRBS data: CDC public domain.
