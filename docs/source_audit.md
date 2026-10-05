# Source and documentation audit

Checked 2026-10-04 by web retrieval. Items marked **[VERIFY]** need the author to confirm them against the downloaded files, because the build sandbox cannot reach cdc.gov.

## YRBS

**A1. Skip patterns (2023, electronic).**
- Source: Brener ND et al. *Overview and Methods for the YRBSS — United States, 2023.* MMWR Suppl 2024;73(4):1–12. doi:10.15585/mmwr.su7304a1.
- The 2023 national survey moved from paper scannable booklets to a tablet survey.
- The tablet version introduced skip patterns. Appropriately skipped questions are coded to a "did not engage" response, not to missing. CDC's example: never smoked → 0 days smoked.
- Electronic administration also added real-time logic checks for invalid entries such as height and weight.

**A2. Site mode, 2023.** Of 68 site surveys, 32 were collected electronically and 36 on paper (same source).

**A3. Editing and quality control.**
- National and site data sets were cleaned and edited for inconsistencies.
- Missing data were not imputed.
- A questionnaire failed quality control if fewer than 20 responses remained after editing, or if it had the same answer to 15 or more consecutive questions.
- 2023 national: 283 of 20,386 questionnaires excluded, leaving 20,103 usable.

**A4. Site questionnaires.** Sites could add or delete questions but had to keep at least 58 of the 87 standard questions, including all demographic questions (2023).

**A5. Earlier years.** The SADC User's Guide (2023) says data sets from earlier years have more missing data because earlier questionnaires did not contain the same standard questions. It also says many state and district surveys dropped some standard questions.

**A6. Unidentifiable mechanisms.** The MMWR 2023 Limitations section says that, from the data, it is not possible to tell whether a response is missing because:
- the question was not on that student's questionnaire,
- the student did not answer, or
- the response was set to missing for being out of range or inconsistent.

This is the core identifiability constraint behind `NA_UNRES` (see `taxonomy.md`).

**A7. Sexual identity.** 2023 response options include "I do not know what this question is asking." **[VERIFY: its numeric code in the SADC formats program.]**

**A8. Weighting.** Site data are weighted only when nonresponse-bias analyses allow it. In 2023, 36 states, 3 tribal governments, 5 territories and 21 districts had weighted data.

**A9. Mode variable.** The SADC User's Guide (2023) does not document a variable for administration mode. **[VERIFY by inspecting the variable list.]** Mode is therefore identifiable only for the national survey: paper through 2021, tablet in 2023.

**A10. Design variables** (SADC User's Guide 2023): `sitecode`, `sitename`, `sitetype` (District / State / National), `sitetypenum`, `year`, `survyear`, `weight`, `stratum`, `PSU`.

**A11. Outcome items** (SADC User's Guide 2023, 2023 numbering):

| Item | Wording | Responses | CDC derived indicator |
|---|---|---|---|
| Q29 | "During the past 12 months, how many times did you actually attempt suicide?" | A = 0 times, B = 1, C = 2–3, D = 4–5, E = 6+ | QN29 = B–E over A–E |
| Q30 | "If you attempted suicide during the past 12 months, did any attempt result in an injury, poisoning, or overdose that had to be treated by a doctor or nurse?" | A = did not attempt, B = yes, C = no | QN30 = B over A–C |

- The QN30 denominator includes students who did not attempt, so QN30 is a **population-level** prevalence, not a share of attempters.
- Q27 (seriously considered) and Q28 (made a plan) are the proximal items.
- **[VERIFY V2: numeric codes are 1..5 and 1..3 in the ASCII file.]**
- **[VERIFY V6: wording unchanged across the audited window.]** The SADC maps earlier years onto 2023 question numbers, but the release notes say comparability needs checking.

**A12. Data availability.**
- The 2023 combined high-school files are available as ASCII (national, district, seven state groups) with SAS and SPSS input programs.
- URLs are recorded in `config/project.yaml` and `scripts/00_acquire.sh`.
- The data are public domain (CDC Stacks record for the User's Guide).

**A13. Population prevalence context, not used for modeling.** The 2023 national report gives 9.5% of students attempting suicide. Rarity in this project is characterized only from the analytic data (`tables/T_prevalence.csv`).

## BRFSS (secondary testbed)

**B1. ACE module, 2023.** Used by 12 states (Delaware, Florida, Georgia, Indiana, Missouri, Nevada, New Jersey, Ohio, Oregon, Rhode Island, Tennessee, Virginia). Ohio fielded it on questionnaire version 1 (`LLCP23V1`, weight `_LCPWTV1`); the rest on the main data set (CDC "2023 Modules by State by Data Set & Weight").
- Absence of ACE data therefore has at least three provenances:
  1. state did not field the module;
  2. state fielded it on a split-sample version only;
  3. respondent nonresponse or breakoff inside the module.

**B2. ACE module nonresponse.** Besera G et al., Am J Prev Med 2024;67(6):941–950.
- 21 states used the module in 2019 and 16 in 2021.
- Module nonresponse (skipping ≥4 ACE domains): 1.2% in 2019, 2.4% in 2021.
- Nonresponse rose as the module progressed and was highest for the sexual-abuse items.
- Directly relevant to the within-module provenance class.

**B3. Outcome.** BRFSS has no standard past-year suicide-attempt item comparable to YRBS Q29.
- The contrasting adult analysis therefore needs its own outcome.
- Default proposed in `protocol.md` §12: ever told depressive disorder (core), with frequent mental distress as the alternate.
- REQUIRES SELORM decision. Not a blocker for the YRBS arm.

## CSTE 2027

The official 2027 call was not posted as of 2026-10-04. Past cycles:
- the call opened around Nov 1 and closed in early January (2023 conference: opened 11/1/2022, closed 1/5/2023);
- abstracts were limited to 400 words, with a separate student-abstract category.

Status: TARGET. See `cste/TRACKER.md`.
