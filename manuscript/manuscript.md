# Distinguishing missingness provenance in youth suicide-attempt prediction: survey omission, questionnaire version, and item nonresponse in the combined Youth Risk Behavior Survey

DRAFT — UNVERIFIED. Results sections are templates. Every `{{key}}` is filled from `results/stats.json` by `manuscript/render.py`. The renderer refuses synthetic-mode statistics.

**Selorm Buaka**¹

¹ University of Northern Colorado · othnielbuaka@gmail.com · ORCID PLACEHOLDER

---

## Abstract

PENDING REAL-DATA RESULTS. Not written until results exist (author instruction).

## Introduction

[DRAFT — to be revised in the author's voice]

### The surveys
- The Youth Risk Behavior Surveillance System (YRBSS) is the main U.S. source of school-based data on adolescent suicidal behavior.
- CDC's combined data sets pool national, state, and large urban district surveys across cycles so that multi-site, multi-year analyses are possible.

### The problem
- In the pooled data, a missing predictor can mean very different things:
  - the jurisdiction removed the question from its questionnaire;
  - the question was not on that year's standard questionnaire;
  - the student did not answer; or
  - CDC set an inconsistent response to missing.
- CDC notes that, at the individual level, these mechanisms cannot be separated in the national data.
- Since the 2023 move to tablet administration, legitimately skipped questions are coded to their implied response rather than left missing.

### Why it matters for prediction
- Prediction studies usually treat all of these as one "missing" category.
- Doing so can let a model learn which survey a student came from rather than anything about the student.

### This study
We built a provenance taxonomy restricted to what the released data can identify. We then asked whether provenance-aware handling changes the discrimination, calibration, and transportability of models for past-year suicide attempt and injurious suicide attempt.

## Methods

### Data
- CDC YRBS 2023 combined high-school data set (state and district surveys; national survey analyzed separately).
- The study window was chosen by pre-stated availability rules: {{window}}.
- Exclusions are shown in the cohort flow tables.

### Outcomes
- **Any past-year suicide attempt:** one or more attempts in the past 12 months (CDC QN29 definition).
- **Injurious suicide attempt:** an attempt resulting in injury, poisoning, or overdose treated by a doctor or nurse, among all respondents (CDC QN30 definition).

### Missingness provenance
- Every predictor cell was assigned one code:
  - observed;
  - observed non-substantive;
  - not asked by the site (missing for all records in that survey while present elsewhere that year);
  - not on that year's questionnaire; or
  - unresolved (missing where asked: nonresponse or edit, indistinguishable).
- Skip-implied values were treated as observed.
- Supplementary Table S1 maps the conceptual sources to these codes.

### Prediction methods
- **Conventional handling:**
  - complete-case analysis;
  - mean imputation;
  - mean imputation with missing indicators;
  - chained-equations multiple imputation (m=5, predictions averaged);
  - gradient boosting with native missing-value handling.
- **Provenance-aware handling:**
  - provenance-specific indicators added to logistic regression and to gradient boosting;
  - pattern submodels fitted per survey availability pattern.
- **Diagnostic models:**
  - site, year, and availability pattern only;
  - demographics only.
- **Merchant method:** [the structure-preserving method developed with W. Merchant — PENDING MATERIALS].
- **Predictor set:** suicidal ideation and planning were excluded from primary models.
- **Fitting:** all preprocessing was fit on training data only, and hyperparameters were fixed in advance.

### Splits and evaluation
- **Splits:**
  - Within each survey, primary sampling units were assigned 60/20/20 to training, validation, and test sets.
  - Alternative structures held out whole jurisdictions or the latest cycle.
- **Metrics** (computed on the test set, unweighted and survey-weighted):
  - AUROC;
  - PR-AUC;
  - Brier score;
  - calibration intercept and slope;
  - threshold metrics at 80% sensitivity and top-5%/10% risk (thresholds chosen on validation).
- **Uncertainty:** 95% CIs from a bootstrap resampling PSUs within strata (1,000 replicates, model held fixed). Method contrasts were paired.

### Survey design
- Prevalence was estimated with weights and Taylor linearization.
- Models were trained unweighted; weighted training was examined as a sensitivity analysis.

### Sensitivity analyses
Thirteen pre-specified scenarios (Supplementary Table S2).

## Results

PENDING REAL-DATA RUN. Template:

- **Cohort and prevalence.**
  - Any attempt: the primary cohort included {{prev_any_attempt_site_level_n}} students, of whom {{prev_any_attempt_site_level_events}} reported any attempt.
  - Injurious attempt: {{prev_injurious_attempt_site_level_n}} students, of whom {{prev_injurious_attempt_site_level_events}} reported an injurious attempt.
  - Weighted prevalence by year: Table 1.
- **Provenance.** [Figure 1 description from T_provenance_overall.]
- **Primary comparisons.** [Table 2; Figure 2. Report each pre-specified contrast with paired CI, e.g. PROV_LR − MIND_LR ΔAUROC {{contrast.any_attempt.S0_primary.PROV_LR - MIND_LR.weighted.auroc}}.]
- **Structure vs individual information.** [STRUCT_ONLY performance; S_LSO and S_FE contrasts; Figure 3.]
- **Calibration and thresholds.** [Figure 4; Table 2 threshold columns.]
- **Subgroups.** [Table 4.]

## Discussion

PENDING. To cover:
- what provenance does and does not add;
- survey-structure learning;
- the deployment context (school or district surveillance vs individual screening);
- PPV at realistic prevalence;
- limitations:
  - unidentifiable mechanisms (C3/C4/C7);
  - QC exclusions not observable;
  - no site-level mode variable;
  - cross-sectional design;
  - self-report.

## Data and code availability
- Data: CDC YRBS public-use combined files.
- Code: [GitHub URL after release]; archived at [Zenodo DOI after deposit].

## Author contributions
Selorm Buaka (sole author): conceptualization, methodology, software, formal analysis, writing – original draft.

## Use of AI tools
- Software, documentation drafts, and analysis scaffolding were produced with an AI assistant (Claude, Anthropic) under the author's direction.
- All analytic decisions, verification, and final text are the author's responsibility.
- [Confirm the target journal's disclosure policy.]
