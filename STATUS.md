# STATUS / TODO — Project 2

Updated 2026-10-10.

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
- Unit and integration tests: 26 passing.
- MacBook one-command runner; Slurm prep → array → report chain; environment files.
- README, variable dictionary, decision log, verification checklist, `AUTHORS.json`, `CITATION.cff`, license.
- Manuscript draft: introduction and methods written; results templated to `stats.json`. Renderer refuses synthetic statistics.
- Supplementary methods draft.
- CSTE tracker, plus a weekly scheduled check for the 2027 call (Mondays 8:47 MT).
- BRFSS arm (`src/p2prov/brfss.py`):
  - acquisition script with verified 2023 URLs;
  - 7 ACE provenance classes, including don't-know/refused, breakoff, state-not-fielded, and version-only;
  - within-state and leave-states-out evaluation;
  - 2 tests on synthetic data.
  - Variable names and codes are pending verification (V13).

## COMPLETE — REAL-DATA RUN (2026-10-10, on the MacBook)
- CDC YRBS 2023 SADC files and BRFSS 2023 (main + version 1) downloaded with checksums.
- Year window 2015–2023 (all five cycles qualify); 1,008,297 records, 250 surveys.
- National 2023 weighted any-attempt prevalence 9.5% = CDC published figure (V7).
- All 26 tasks fitted and evaluated; BRFSS testbed run.
- Fixes found on real data: character-coded q items, 4 ambiguous variable matches (config/variable_map.yaml),
  QN22 not-applicable coding, real skip gates, calibration on singular subgroups, bootstrap strata (see DECISIONS).
- Open checks resolved: S_THR95 = S0 because no item is 95–99.99% missing in any survey; Indiana has no ACE
  responses in the public BRFSS main file despite CDC's module list (flagged).

- CIs re-evaluated with survey-level bootstrap strata (primary 1,000 reps; sensitivity 200; BRFSS 50).
- Results preprint DRAFT written (Docs): https://claude.ai/code/artifact/8e74d553-f742-459f-b8ea-c2d2b48ab46a
  — not for posting until verification, authorship, and [VERIFY] references are resolved.

- Journal shortlist: AJE (Practice of Epidemiology) → Annals of Epidemiology → BMC Med Res Methodol (`docs/journals.md`).
- References verified (Sperrin, Fletcher Mercaldo & Blume, MacNell, Collins); search log started (`docs/search_log.csv`).

- Poster draft (Design canvas, landscape Letter; resize when CSTE posts specs): https://claude.ai/artifact/4UTwja189R5zBkYq6RGcpE

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
- Confirm ORCID 0009-0005-3991-4859 may replace the placeholder in `AUTHORS.json`.
- Confirm the 4 variable choices in `config/variable_map.yaml` (V3).
- Indiana BRFSS ACE question (versions 2/3 not downloaded).
- Discuss Dr. Merchant's authorship.

## PENDING REAL-DATA RUN
- Verification items V6, V8, V9 and V12 (V7 checked).
- CSTE abstract (after results and the official 2027 call).
- Seed-repetition runs for model-fitting variance (HPC).
- Repeat-attempt outcome: not added (test sets already scored; would now be post hoc).
- Full 1,000-replicate CIs for sensitivity scenarios (HPC).

## TO BUILD NEXT (no blocker)
- GitHub push and Zenodo deposit: guide written (`docs/PUBLISH_GUIDE.md`). Needs your token, or your own push. Release only after verification.

## VERIFIED
- (none yet)
