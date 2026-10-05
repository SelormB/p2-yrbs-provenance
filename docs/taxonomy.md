# Missingness-provenance taxonomy for the YRBS combined high-school data

DRAFT — UNVERIFIED. Section references are to the source audit (`docs/source_audit.md`).

Not every source of absent information in YRBS is "structural missingness," and not every source can be seen in the released file. This taxonomy separates three things:

- the **conceptual sources** of absence that CDC documentation describes;
- what the **released combined (SADC) data can identify**;
- the **code** the pipeline assigns to each cell.

## 1. Conceptual sources

| # | Source | What happens | CDC basis |
|---|---|---|---|
| C1 | Genuinely observed response | The student answered the item. | — |
| C2 | Legitimate skip (electronic administration) | The student was not shown a follow-up item. CDC codes it to the logically implied response (for example, never smoked → 0 days smoked), **not** to missing. | A1 |
| C3 | Item nonresponse | The item was shown and left blank. | A3 |
| C4 | Consistency / out-of-range edit | An answer conflicting with other answers, or out of range, is set to missing by CDC's edits. | A3 |
| C5 | Site-level question omission | The site's questionnaire did not include the item. Sites must keep at least 58 of the 87 standard questions, including all demographics. | A4 |
| C6 | Questionnaire-version absence | The item was not on that year's standard questionnaire. In the combined file, it is absent for everyone that year. | A5 |
| C7 | National/site overlap | A student in a school sampled by both the national and a site survey answered only the site questionnaire. Their national record lacks items the site did not ask. | A6 |
| C8 | Quality-control exclusion | A questionnaire with fewer than 20 responses after editing, or with 15 or more identical consecutive answers, is removed entirely. | A3 |
| C9 | Non-substantive response | For example, "I do not know what this question is asking" on sexual identity. | A7 |
| C10 | Design exclusion / unweighted survey | A site whose data could not be weighted as representative. The weight is absent. | A8 |

## 2. Identifiability in the released data

| Source | Identifiable from the released data? | How |
|---|---|---|
| C1 | Yes | Value present. |
| C2 | **Partly.** The skip-implied value is in the data and is indistinguishable from an answered value of the same code. | Flag `SKIP_CONSISTENT` when the gate item says "did not engage" and the dependent item holds the implied code. In paper surveys these values were answered; in electronic surveys they may be skip-coded. The combined file has no mode variable (A9), so the flag is descriptive only. |
| C3 | **No, not separately** | Pooled into `NA_UNRES`. |
| C4 | **No, not separately** | Pooled into `NA_UNRES`. CDC says these cannot be told apart (A6). |
| C5 | Yes, at survey level | An item 100% missing within a site-year survey, while present in other surveys that year, is coded `NA_SITE`. |
| C6 | Yes | An item absent from every survey in a year is coded `NA_YEAR`. |
| C7 | **No** | Individual-level, national file only. Pooled into `NA_UNRES`. This is one reason the national survey is analyzed separately (scenario S_NAT). |
| C8 | Not in data | Excluded records are not released. This is a selection mechanism, documented as a limitation. |
| C9 | Yes, if the response code is known | Coded `OBS_NONSUB`. The response codes are configured only after author verification (V4). |
| C10 | Yes | The weight is missing. These surveys are excluded from the primary cohort and included in S_UNWT. |

## 3. Cell codes used by the pipeline

| Code | Meaning | Conceptual sources it contains |
|---|---|---|
| `OBS` | Observed substantive value | C1, and C2 where skip-coded |
| `OBS_NONSUB` | Observed non-substantive value | C9 |
| `NA_SITE` | Not asked: site omission | C5 |
| `NA_YEAR` | Not asked: not on that year's questionnaire | C6 |
| `NA_UNRES` | Missing where asked, mechanism unresolved | C3 + C4 (+ C7 in national data) |

Every cell receives exactly one code (unit test `test_provenance_covers_every_cell`).

## 4. Threshold for "not asked"

Primary rule: an item counts as not asked in a survey when it is missing for **100%** of that survey's records.

Sensitivity rule (S_THR95): **≥95%**. This catches surveys that asked an item of only a small subsample, or where almost all values were edited away. If results move materially between the two rules, the boundary between C5 and C3/C4 is shaping the findings, and this will be reported.

## 5. What this means for the analysis

- `NA_SITE` and `NA_YEAR` describe the **survey**, not the student. A model that learns from them can learn *which survey a student came from*. Survey prevalence differs by site and year, so that can improve apparent performance without telling us anything about the individual student. Two checks address this:
  - the `STRUCT_ONLY` diagnostic model (site, year, and availability pattern only);
  - the leave-sites-out split (S_LSO).
- `NA_UNRES` is the only code that plausibly carries student-level information. Item nonresponse on sensitive items may track risk. It is also contaminated by CDC edits, so a coefficient on it cannot be read as a "nonresponse effect."
- Skip-implied values are **observed** values. They are not imputed and not treated as missing, in line with CDC coding.
