# Literature review (working draft)

DRAFT — UNVERIFIED.

**Citation tags:**
- **[V-web]** — existence and bibliographic details were checked by web retrieval on 2026-10-04.
- **[VERIFY]** — recalled; the author must confirm the details before any citation is used.

No citation goes into the manuscript until it has been confirmed against the source.

## 1. The problem in YRBS specifically

**Absence has several causes.** In the combined YRBS files, the same blank cell can mean:
- a site did not ask the question;
- the question was not on that year's questionnaire;
- the student skipped it;
- CDC edited an inconsistent answer to missing; or
- (national file) the student received a site questionnaire.

CDC states that these cannot be told apart at the individual level (Brener 2024 **[V-web]**).

**Electronic skips are coded, not left missing.** In the 2023 national survey, legitimately skipped items are filled with the implied "did not engage" value (Brener 2024 **[V-web]**). Skip logic therefore does not create missing values in the release, but it does change what an observed value means.

**Mode changes do not appear to shift prevalence.** Mode-comparison studies report no meaningful shift in prevalence estimates from electronic vs paper administration (Bryan 2022, J Sch Health; Li 2024, J Adolesc Health — both cited in Brener 2024 **[V-web]**). That does not settle whether mode alters missingness patterns. To our reading, no published study has asked that question **[to confirm in the systematic search]**.

**Recent prevalence context.** Mental health and suicide-risk prevalence for 2023 is reported in Verlenden 2024, MMWR Suppl 73(4):79–86 **[V-web via Brener 2024 refs]**.

## 2. Prediction of adolescent suicide attempt

**General context.** Risk-factor research has shown weak individual-level prediction from single factors (Franklin 2017, Psychol Bull 143:187–232 **[VERIFY]**). Prediction models for suicide attempts tend to have low positive predictive value at population prevalence (Belsher 2019, JAMA Psychiatry 76:642–651 **[VERIFY]**). This is why the project reports PPV and NPV at capacity-based thresholds and characterizes rarity empirically.

**Machine learning on youth risk-behavior surveys** is an active area. Records identified 2026-10-04, to be screened in the systematic search below:
- Explainable ML prediction of adolescent suicide attempts in a national survey (PubMed 42487762, 2026; dataset and country to be confirmed) **[V-web: record exists]**.
- Classifying suicide attempts from ideation in adolescents using ML (PMC12436705) **[V-web: record exists]**.
- Korea Youth Risk Behavior Survey ML comparisons (J Korean Acad Psychiatr Ment Health Nurs 2025) **[V-web: record exists]**.
- Prediction of suicidal thinking validated across three cohorts (JMIR 2024;26:e55913) **[V-web]**.

**Gap to confirm by systematic search.** As far as we can tell, existing YRBS and YRBS-style prediction work treats missing predictor values with complete-case analysis or a single imputation. None appears to separate site omission and questionnaire-version absence from item nonresponse, or to test whether apparent performance reflects survey structure.

## 3. Missing data in prediction (methods basis for the comparators)

**Missingness mechanisms.** Rubin 1976, Biometrika 63:581–592; Little & Rubin, *Statistical Analysis with Missing Data*, 3rd ed., 2019 **[VERIFY]**.

**Prediction differs from inference.** Missing-data handling for prediction should match what is available at deployment. Missing indicators and imputation without the outcome are legitimate for prediction even where they bias causal estimates:
- Sperrin, Martin, Sisk, Peek 2020, J Clin Epidemiol **[V-web: title/journal; volume and pages VERIFY]**.
- Sisk, Sperrin, Peek, van Smeden, Martin 2023, Stat Methods Med Res — simulation of imputation and missing indicators across development and deployment **[V-web]**.

**Cautions on missing indicators.** "A cautionary note on the use of the missing indicator method for handling missing data in prediction research," J Clin Epidemiol 2020 **[V-web: title; authors VERIFY — believed van Smeden, Groenwold, Moons]**. Motivates reporting `MIND_LR` alongside the alternatives rather than as the default.

**Multiple imputation by chained equations.** van Buuren & Groothuis-Oudshoorn 2011, J Stat Softw 45(3) **[VERIFY]**. Implemented with scikit-learn `IterativeImputer` (posterior sampling, m=5).

**Pattern submodels:**
- Mercaldo & Blume, "Missing data and prediction: the pattern submodel," Biostatistics 2020 **[V-web: title; volume and pages VERIFY]**. Basis for `PATTERN_LR`.
- Stempfle, Panahi, Johansson, "Sharing pattern submodels for prediction with missing values," AAAI 2023 **[V-web]**.

**Trees and missing values:**
- Twala, Jones, Hand 2008, Pattern Recognit Lett 29:950–956 — missing incorporated in attributes **[VERIFY]**.
- Josse, Prost, Scornet, Varoquaux, "On the consistency of supervised learning with missing values" (arXiv 2019; journal version VERIFY).

## 4. Complex survey design and prediction

**Weights in boosting.** MacNell et al. 2023, PLoS One 18:e0280387 — effect of sampling weights in gradient boosting **[V-web]**. A 2024 Annals of Epidemiology paper reports that complex sampling structures may not be needed for prediction models with imbalanced outcomes (ScienceDirect S1047279724002886) **[V-web: record; authors VERIFY]**. Together these motivate treating weighted training as a sensitivity analysis rather than a default.

**Design-based variance:**
- Lumley 2004, J Stat Softw 9(8) **[VERIFY]**.
- Rao & Wu 1988, JASA 83:231–241 — bootstrap for complex surveys **[VERIFY]**.

## 5. Evaluation and reporting standards

- Calibration: Van Calster et al. 2019, BMC Med 17:230 **[VERIFY]**.
- Reporting: Collins et al. 2024, TRIPOD+AI, BMJ 385:e078378 **[VERIFY]**.
- Steyerberg, *Clinical Prediction Models*, 2nd ed., 2019 **[VERIFY]**.

## 6. BRFSS ACE module

- Besera G, Annor FB, Swedo EA, Aslam MV, Massetti GM. ACE module nonresponse, BRFSS 2019 and 2021. Am J Prev Med 2024;67(6):941–950 **[V-web]**.
- CDC BRFSS "2023 Modules by State by Data Set & Weight" **[V-web]**.

## 7. Merchant branching-survey work

The co-authored branching-survey manuscript is the methodological foundation for RQ5.
- **REQUIRES MERCHANT METHOD MATERIALS.**
- Citation details to be supplied by the author.

## Systematic search — PENDING (in STATUS)

**Databases:** PubMed, Scopus, ERIC.

**Search string (draft):**
- ("Youth Risk Behavior Survey" OR YRBS OR "school-based survey")
- AND (suicid*)
- AND (predict* OR "machine learning" OR classif*)
- AND (missing* OR imput* OR "skip pattern" OR "item nonresponse")

**Second string (methods):**
- ("skip pattern" OR "branching" OR "structural missing" OR "not applicable")
- AND (imputation OR prediction)
- AND survey

Screening log to be kept in `docs/search_log.csv`.
