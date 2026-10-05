# STATUS / TODO — Project 2

Updated 2026-10-04.

Legend:
- COMPLETE — done.
- IN PROGRESS — being worked on.
- BLOCKED — waiting on something external.
- REQUIRES SELORM — needs your decision or action.
- REQUIRES MERCHANT MATERIALS — needs the co-authored method manuscript.
- PENDING REAL-DATA RUN — code is ready; waiting on CDC files.
- VERIFIED — author has checked it.

## COMPLETE
- Source audit for the YRBS 2023 methods: skip coding, edits, QC rule, site questionnaire flexibility, mode by site, weighting, outcome items Q29/Q30 and QN definitions, design variables (`docs/source_audit.md`).
- Missingness-provenance taxonomy, including an identifiability table (`docs/taxonomy.md`).
- Research questions, hypotheses, and the analysis protocol, including the survey-design table and leakage controls (`docs/protocol.md`).
- Acquisition script with checksums, using exact CDC URLs (`scripts/00_acquire.sh`).
- Fixed-width reader driven by CDC's SAS input program; concept-to-variable resolver.
- Provenance labelling; availability maps; skip-consistency and outcome-pair diagnostics.
- Year-window audit with pre-stated rules.
- Cohort construction with flow tables; design IDs made unique per site-year.
- Frozen, hashed splits: within-survey PSU, leave-sites-out, temporal. PH-MissBench adapter included.
- Ten comparators: 5 conventional, 3 provenance/structure-aware, 2 diagnostic.
- Merchant integration point.
- Survey-weighted and unweighted metrics, design-based bootstrap, paired contrasts, validation-chosen thresholds, calibration, subgroups.
- 13 sensitivity scenarios × 2 outcomes.
- Figures (provenance map, AUROC forest, contrasts by scenario, calibration); publication tables; `stats.json`.
- Unit and integration tests: 24 passing.
- MacBook one-command runner; Slurm prep → array → report chain; environment files.
- README, variable dictionary, decision log, verification checklist, `AUTHORS.json`, `CITATION.cff`, license.
- Manuscript draft: introduction and methods written; results templated to `stats.json`. Renderer refuses synthetic statistics.
- Supplementary methods draft.
- CSTE tracker.

## IN PROGRESS
- Literature review: framework written. Systematic search and screening log still to do.

## BLOCKED — REQUIRES MERCHANT MATERIALS
- `MERCHANT_SP` method (`src/p2prov/methods.py`), RQ5, and the related manuscript text.

## REQUIRES SELORM
- Run `bash scripts/run_local.sh` on the MacBook. CDC is not reachable from the build workspace.
- PH-MissBench YRBS split file (`data/external/phmissbench_yrbs_split.parquet`). Alternatively, confirm that PH-MissBench's YRBS module is not frozen yet; the P2-internal split is then primary.
- Verification items V1–V5 and V10–V11 (`docs/VERIFICATION.md`).
- BRFSS outcome choice. Default: ever told depressive disorder; alternate: frequent mental distress.
- UNC cluster account and partition details (`slurm/site.env`).
- ORCID iD for `AUTHORS.json`.
- Discuss Dr. Merchant's authorship.

## PENDING REAL-DATA RUN
- Year window, prevalence and rarity characterization, provenance maps, the 26 tasks, figures and tables.
- Verification items V6–V9 and V12.
- Journal recommendation (2–3 journals, after results).
- CSTE abstract (after results and the official 2027 call).
- Poster material.
- Seed-repetition runs for model-fitting variance (HPC).
- Decision on adding a repeat-attempt outcome definition. Must be made before test-set scoring.

## TO BUILD NEXT (no blocker)
- BRFSS arm: acquisition script for LLCP2023 and LLCP23V1, ACE-module provenance classes, cohort.
- (moved) CSTE 2027 monitoring: COMPLETE — weekly scheduled check, Mondays 8:47 MT.
- GitHub repository push. Needs a token or the author's push; see the publish guide when it is ready.

## VERIFIED
- (none yet)
