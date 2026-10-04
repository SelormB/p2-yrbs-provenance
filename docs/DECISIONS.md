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
