# Analysis protocol — Project 2

DRAFT — UNVERIFIED. Version 0.1, 2026-10-04.

This protocol is written before any real-data test-set scoring. Changes after that point are logged in `DECISIONS.md` with a date and labelled post hoc wherever they appear.

## 1. Question

In the CDC YRBS combined high-school data, apparently missing predictor information comes from distinguishable sources (`taxonomy.md`). The question is: **does distinguishing missingness provenance change the discrimination, calibration, and transportability of models predicting past-year suicide attempt and injurious suicide attempt**, compared with conventional missing-data handling? And how much of any apparent gain reflects survey structure (site and year) rather than student-level information?

## 2. Research questions and hypotheses

**RQ1 (description).** How is missing predictor information distributed across provenance classes, items, years, and site types?
- H1: site omission (`NA_SITE`) and questionnaire-version absence (`NA_YEAR`) account for more absent cells than unresolved missingness (`NA_UNRES`) in the state/district data.

**RQ2 (primary comparison).** Do provenance-aware methods improve discrimination or calibration over the matched conventional methods? Pre-specified paired contrasts, on the same test rows:
- `PROV_LR` vs `MIND_LR` — the effect of splitting the single missing indicator by provenance.
- `PATTERN_LR` vs `MEAN_LR` — the effect of fitting separate models by survey availability pattern instead of imputing not-asked items.
- `PROV_HGB` vs `HGB_NATIVE` — provenance indicators on top of native missing-value handling.
- `PROV_LR` vs `MICE_LR` — provenance encoding vs multiple imputation.

H2: differences in AUROC are small (|ΔAUROC| < 0.01). Gains, if any, appear mainly in calibration across surveys (calibration intercept by site type and year). This is stated as a hypothesis, not a result.

**RQ3 (structure vs individual information).** How close does a model using only site, year, and availability pattern (`STRUCT_ONLY`) come to the individual-level models? Do provenance-aware advantages survive leave-sites-out evaluation?
- H3: any advantage of provenance indicators shrinks under leave-sites-out evaluation.

**RQ4 (outcome and prevalence).** Do conclusions differ between any attempt and injurious attempt?

**RQ5 (Merchant method).** Does the branching / structure-preserving method developed with Dr. William Merchant change RQ2's answer?
- **BLOCKED — REQUIRES MERCHANT METHOD MATERIALS.**

## 3. Data

**Primary.** CDC YRBS 2023 combined high-school data set (SADC), state and district surveys.
- Rationale: site-level question omission, the central phenomenon, exists only in site surveys.

**Secondary.** National YRBS, analyzed separately (S_NAT).
- Rationale: different sampling design; individual-level overlap missingness (taxonomy C7); a known 2023 mode change.

National and site records are never pooled in a model.
- The two represent different populations.
- Pooling their weights produces no coherent target population.

## 4. Study window

### 4.1 Candidate
2015, 2017, 2019, 2021, 2023.

### 4.2 Rules
Applied by `scripts/03_audit_years.py` → `results/audit/window.json`. A year qualifies when:
- each outcome item is asked in ≥50% of that year's surveys; and
- ≥80% of predictor concepts are on that year's questionnaire.

The window is the longest contiguous run of qualifying years; the later run wins ties. Failing years are reported, not hidden.

### 4.3 Known breaks, handled by sensitivity rather than exclusion
- 2021: fall administration during COVID-19 → S_NO2021.
- 2023: national tablet administration plus a mixed-mode site year → S_PRE2023 and S_ONLY2023.

## 5. Outcomes

| Outcome | Item | Positive | Valid denominator |
|---|---|---|---|
| Any past-year suicide attempt | Q29 | 1 or more times | All valid Q29 responses |
| Injurious suicide attempt | Q30 | Attempt treated by a doctor or nurse | All valid Q30 responses, including "did not attempt" (CDC QN30 definition) |

- Both are as defined by CDC (`source_audit.md` A11).
- Records with a missing outcome are excluded. Their provenance is reported (`tables/T_outcome_pair_missingness.csv`).
- Rarity is described from the observed weighted and unweighted prevalence only (`tables/T_prevalence.csv`).

## 6. Splits

### 6.1 PH-MissBench
- The frozen PH-MissBench YRBS split is used as the primary split if it covers every cohort row with train / valid / test labels.
- Otherwise it is declared incompatible and the P2-internal split is used. The PH-MissBench test set is never modified.
- **Status: REQUIRES SELORM** (split file not provided).

### 6.2 P2-internal primary split
- PSUs are assigned 60/20/20 to train / valid / test within each site-year survey, with seed 20261004.
- Surveys with fewer than 3 PSUs are assigned at record level.
- Within-survey assignment keeps every survey represented in the test set.

### 6.3 Alternative structures
- **Leave-sites-out** (S_LSO): whole jurisdictions held out across all years.
- **Temporal** (S_TEMP): the latest cycle is the test set.

### 6.4 Freezing
Each split is hashed (SHA-256) and frozen. The pipeline refuses to overwrite a frozen split that differs.

## 7. Comparators

The final set is chosen for relevance, not breadth.

| Name | Role | Handling | Why it is here |
|---|---|---|---|
| `CC_LR` | Conventional | Complete-case | Reference point. It predicts only for complete rows, so coverage is reported alongside it. |
| `MEAN_LR` | Conventional | Training-mean imputation | The simplest deployable approach. |
| `MIND_LR` | Conventional | Mean imputation + one missing indicator per item | Common practice for prediction. Defensible for prediction when missingness is informative and stable between development and deployment (Sperrin 2020; Sisk 2023). |
| `MICE_LR` | Conventional | Chained-equations imputation, m=5, posterior draws, outcome excluded, predictions averaged | Model-based imputation that remains usable at deployment. |
| `HGB_NATIVE` | Conventional | Gradient boosting with native missing-value routing | Missing-incorporated-in-attributes behavior (Twala 2008; Josse 2019). |
| `PROV_LR` | Provenance-aware | Mean imputation + separate not-asked / unresolved / non-substantive indicators | Isolates the value of knowing *why* a value is absent. |
| `PROV_HGB` | Provenance-aware | Native missing handling + provenance indicators | Same question for the flexible model. |
| `PATTERN_LR` | Structure-aware | One model per survey availability pattern ("sharing" pattern submodel) | Mercaldo & Blume 2020. Never imputes an item the survey did not ask. |
| `STRUCT_ONLY` | Diagnostic | Site, year, and availability pattern only | Measures what survey structure alone predicts. |
| `DEMO_LR` | Diagnostic | Demographics only | Floor. |
| `MERCHANT_SP` | Structure-preserving | — | **BLOCKED — REQUIRES MERCHANT METHOD MATERIALS.** |

**Predictors.**
- CDC dichotomous QN indicators for 15 behavioral and experiential concepts, resolved from CDC labels and author-verified (V3).
- Demographics (age, sex, grade, race/ethnicity, sexual identity) with an explicit missing level.
- Excluded from primary models: suicidal ideation and planning (Q27/Q28), as same-construct proximal items (added in S_PROX).
- Excluded from individual-level models: site and year identifiers (added in S_FE).

**Hyperparameters.** Fixed in advance, with no tuning on validation data, to limit analytic flexibility.
- Logistic regression: L2 penalty, C = 1.
- Gradient boosting: learning rate 0.05, up to 500 iterations with early stopping on an internal 15% slice of the training data, 31 leaves, ≥50 samples per leaf.

## 8. Leakage controls

1. Imputers, means, category levels, and indicator columns are fit on training rows only (unit test `test_imputer_fit_on_training_only`).
2. The outcome is excluded from imputation models.
3. Thresholds are chosen on the validation set and applied unchanged to the test set (`test_thresholds_use_validation_only…`, `thresholds__*.csv`).
4. PSU-level assignment: no school cluster straddles train and test (`test_split_no_psu_straddles…`).
5. Provenance labels are survey-level properties computed from all records of a survey. This does not use the outcome or any test label, and it is the information available at deployment.
6. Splits are frozen before model fitting.

## 9. Survey design: where weights, strata, and PSUs enter

| Stage | Design used? | Approach | Justification |
|---|---|---|---|
| Descriptive prevalence | **Yes** | Weighted estimate; Taylor-linearized SE with strata and PSUs made unique per site-year (with-replacement PSU approximation) | Population estimates require the design (CDC analytic practice, A3). |
| Model development | **No (primary)**; normalized weights in S_WTRAIN | Unweighted fitting | The target is individual risk ranking, not a population parameter. Weighting the fit inflates variance and has given mixed results for boosting (MacNell 2023). Tested as a sensitivity rather than assumed. |
| Performance estimation | **Both** | Unweighted (analytic sample) and survey-weighted (population of students in participating jurisdictions) | Weighted metrics show how the model would perform across the represented student population. |
| Uncertainty | **Yes** | Bootstrap resampling of PSUs with replacement within strata (n_h draws), on the test set, with the model held fixed. 1,000 replicates (50 in dev runs). Paired contrasts use common draws. | Respects clustering; the percentile CI does not assume normality. |
| Subgroups | **Yes** | Weighted metrics within domains (CDC domain approach). Reported only with ≥30 events. | Avoids unstable small-domain estimates. |

**Limitation.** The fixed-model test-set bootstrap does not capture model-fitting variability. The variance contribution of refitting is examined through seed repetition on HPC (planned; see STATUS).

## 10. Evaluation

**Overall metrics:**
- AUROC
- PR-AUC (step-wise average precision)
- Brier score
- Calibration intercept (calibration-in-the-large, logistic recalibration with an offset)
- Calibration slope
- Calibration curves by risk decile

**Thresholds** (chosen on validation):
- 80% sensitivity;
- top 10% and top 5% of predicted risk — screening-capacity framings relevant to school or district programs.

At each threshold: sensitivity, specificity, PPV, NPV, and flagged share.

**Subgroups:** sex, grade, race/ethnicity, sexual identity, site type, year.

## 11. Sensitivity analyses

All listed in `src/p2prov/scenarios.py`:

| Scenario | What changes |
|---|---|
| S_LSO | Leave-sites-out split |
| S_TEMP | Temporal split |
| S_NAT | National survey only |
| S_NO2021 | 2021 excluded |
| S_PRE2023 | 2023 excluded (paper era) |
| S_ONLY2023 | 2023 only |
| S_DROPABS | Items not asked in >30% of surveys dropped |
| S_THR95 | 95% not-asked threshold |
| S_PROX | Q27/Q28 added |
| S_FE | Site and year fixed effects added |
| S_WTRAIN | Weighted training |
| S_UNWT | Unweighted surveys included |

- Each scenario is run for both outcomes.
- **Outcome definition** is covered by the two outcomes. Repeat attempt (Q29 ≥ 2–3 times) is a candidate addition, to be decided before real-data scoring.
- **Mode.** Electronic vs paper is identifiable only for the national file. Site-level mode is not in the released data (A9), so a site-level mode comparison is not attempted. This is reported as a limitation.

**Structure-learning checks:**
1. `PROV_LR − STRUCT_ONLY` and `MIND_LR − STRUCT_ONLY` contrasts.
2. S_LSO vs S0 change in each primary contrast.
3. S_FE: if adding site and year fixed effects absorbs the provenance-indicator advantage, the advantage was survey structure.

## 12. BRFSS contrasting testbed (secondary)

**Default outcome.** Ever told a depressive disorder (core).
- Alternate: frequent mental distress, ≥14 poor-mental-health days.
- REQUIRES SELORM confirmation. BRFSS has no YRBS-equivalent suicide-attempt item.

**Predictors.** ACE module items, plus core demographics and health.

**Provenance classes:**
1. State did not field the module.
2. Module fielded on a split-sample version (version-specific weights).
3. Within-module item nonresponse or breakoff (Besera 2024).
4. Interviewer-administered branching in core sections, coded per CDC codebook.

**Design.** CDC-recommended weight per data set and version; `_STSTR` and `_PSU` for variance.

**Status.** Design specified; acquisition and code PENDING (STATUS).

## 13. Reporting

- TRIPOD+AI items, adapted for a methods comparison (Collins 2024).
- Every number in the manuscript is interpolated from `results/stats.json`.
- Synthetic-fixture outputs are stamped "SYNTHETIC — NOT A SCIENTIFIC RESULT" and are never reported.
