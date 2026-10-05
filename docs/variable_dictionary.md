# Variable dictionary

The final, author-verified map is written by the pipeline to `results/audit/variable_map.csv` (predictors). This page lists the fixed variables and the predictor concepts.

## Design (SADC User's Guide 2023, verified)

| Variable | Meaning | Use |
|---|---|---|
| `sitecode` | Survey site code | survey_id, leave-sites-out unit, provenance grouping |
| `sitename` | Site name | labels |
| `sitetype` | District / State / National | population definition, subgroup |
| `year` | 4-digit survey year | window, provenance, subgroup |
| `weight` | Analytic weight | weighted prevalence and metrics; blank = unweighted survey |
| `stratum` | Stratum | made unique as `design_stratum` = site\|year\|stratum |
| `psu` | Primary sampling unit | made unique as `design_psu`; split and bootstrap unit |

## Outcomes (verified wording; codes VERIFY V2)

| Derived | Source | Positive | Denominator |
|---|---|---|---|
| `y` (any_attempt) | `q29` | codes 2–5 (1 or more attempts) | codes 1–5 |
| `y` (injurious_attempt) | `q30` | code 2 (attempt treated by doctor/nurse) | codes 1–3 (incl. "did not attempt") |

## Proximal items (S_PROX only)

`qn27` seriously considered attempting suicide; `qn28` made a suicide plan.

## Demographics (categorical, explicit missing level)

`age`, `sex`, `grade`, `race7`, `sexid`

## Predictor concepts (resolved from CDC labels; VERIFY V3)

| Concept | Label pattern |
|---|---|
| sad_hopeless | sad or hopeless |
| bullied_school | bullied on school property |
| bullied_electronic | electronically bullied |
| fight | physical fight |
| weapon | carried a weapon |
| forced_sex | physically forced to have sexual intercourse |
| dating_violence | physically hurt … dating |
| unsafe_skip | did not go to school because … unsafe |
| alcohol_current | current alcohol use |
| marijuana_current | current marijuana use |
| vape_current | electronic vapor products |
| cig_current | smoked cigarettes |
| rx_opioid | prescription pain medicine without prescription |
| sleep | hours of sleep |
| grades | grades in school |

Coding: QN 1 = yes → 1, 2 = no → 0, other/blank → missing (VERIFY V4).

## Provenance columns

`prov__<item>` ∈ {OBS, OBS_NONSUB, NA_SITE, NA_YEAR, NA_UNRES}. See `taxonomy.md`.
