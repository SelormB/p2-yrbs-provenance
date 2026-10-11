# Decision log

Each entry gives the date, the decision, the reason, and whether it was made before (pre) or after (post hoc) real-data test-set scoring.

| Date | Decision | Reason | Timing |
|---|---|---|---|
| 2026-10-04 | YRBS primary; BRFSS a secondary contrasting testbed | Author instruction | pre |
| 2026-10-04 | Skip-implied values treated as observed, not missing | CDC codes skipped items to the implied response (MMWR 2024 Suppl 73(4)) | pre |
| 2026-10-04 | Primary population = state + district surveys; national analyzed separately, never pooled in a model | Site omission exists only in site surveys; pooled national+site weights have no coherent target population | pre |
| 2026-10-04 | Q27/Q28 (ideation, plan) excluded from primary predictors; added in S_PROX | Same-construct proximal items dominate prediction and obscure the missing-data comparison | pre |
| 2026-10-04 | Site/year identifiers excluded from individual models; added in S_FE | So that the provenance-vs-structure question can be tested | pre |
| 2026-10-04 | Unweighted model training; weights in evaluation; weighted training as sensitivity | Prediction target is individual ranking; evidence on weighted boosting is mixed | pre |
| 2026-10-04 | Fixed hyperparameters, no validation tuning | Limit analytic flexibility across 10 methods × 13 scenarios × 2 outcomes | pre |
| 2026-10-04 | PSU-level split within survey; frozen with SHA-256 | Prevent cluster leakage; never modify test set | pre |
| 2026-10-04 | "Not asked" = 100% missing in a survey; 95% in S_THR95 | Conservative primary rule | pre |
| 2026-10-04 | Year-window rules: outcome asked in ≥50% of surveys, ≥80% of predictor concepts on questionnaire; longest contiguous run | Pre-stated so the window is not chosen by results | pre |
| 2026-10-04 | MICE imputation model fit on a ≤200,000-row seeded training subsample | Runtime on ~10^6 records; predictions still made for all rows | pre |
| 2026-10-04 | Thresholds: 80% sensitivity, top 10%, top 5% (validation-chosen) | Capacity-based framings for school or district screening | pre |
| 2026-10-10 | Variable map set for 4 ambiguous concepts: fight = qn16, dating violence = qn22, vaping = qn36, cigarettes = qn33 (`config/variable_map.yaml`) | Labels in the 2023 SADC SAS program; automatic matching found several candidates | pre |
| 2026-10-10 | QN22 missing for "did not date" (q22 = 1) coded OBS_NONSUB (structural not-applicable), not NA_UNRES | CDC's QN22 sets non-daters to missing; treating them as nonresponse would mislabel provenance | pre |
| 2026-10-10 | Real skip gates: q31=2 → q33=1, q35=2 → q36=1 | 2023 SADC formats program ($H31S, $H33S, $H35S, $H36S) | pre |
| 2026-10-10 | Ingest keeps only 2015–2023 records, read in chunks | Memory on an 8 GB laptop | pre |
| 2026-10-10 | First full pass uses 50 bootstrap replicates (preliminary CIs); 1,000 replicates for the primary analyses next, sensitivity analyses on HPC | Runtime on the 8 GB MacBook | pre |
| 2026-10-10 | **Bootstrap variance strata changed from the survey's design strata to the whole survey (site × year); PSUs still resampled with replacement.** Point estimates unchanged; all CIs recomputed | Diagnostic after the first real run: 1,874 of 2,908 design strata (64%) held a single test-set PSU, which the bootstrap leaves fixed, so CIs were too narrow. With survey strata, 1 of 235 is a singleton. Survey-level strata ignore within-survey stratification, which is conservative | **post hoc** (method fix, made before reading any CI-based conclusion; logged here and in the preprint) |
| 2026-10-10 | Sensitivity scenarios evaluated with 200 bootstrap replicates; primary with 1,000 | Laptop runtime | pre-report |
| 2026-10-10 | S_THR95 gives results identical to S0 | Checked: no survey had any item 95–99.99% missing; site omission in the release is all-or-nothing, so the two rules label the same cells | finding |
| 2026-10-10 | BRFSS: Indiana listed by CDC as using the ACE module in 2023, but the public main file has no ACE responses for Indiana (10,993 records); coded NA_STATE. Versions 2 and 3 not downloaded | Data check; REQUIRES SELORM / CDC confirmation | finding |
| 2026-10-10 | Authorship: Selorm Buaka, sole author | Author decision | — |
