# Author verification checklist

Nothing is published or submitted until every item is checked by Selorm Buaka personally.

| ID | Check | How | Status |
|---|---|---|---|
| V1 | The CDC files downloaded are the 2023 SADC high-school release | Compare `data/raw/SHA256SUMS.txt` with `results/audit/data_provenance.csv`; open the User's Guide title page | REQUIRES SELORM |
| V2 | Q29 codes 1–5 and Q30 codes 1–3 match the SADC formats program; Q29/Q30 wording is unchanged across the audited window | `2023-SADC-SAS-Formats-Program.sas`; questionnaires for each year | REQUIRES SELORM |
| V3 | Each predictor concept resolved to the right QN variable | `results/audit/variable_map.csv`; fix anything in `config/variable_map.yaml` | REQUIRES SELORM |
| V4 | QN indicators are coded 1 = yes, 2 = no; sexual-identity "do not know what this question is asking" code | Formats program | REQUIRES SELORM |
| V5 | Real skip-gate pairs and implied codes for 2023 | 2023 questionnaire + formats; then set `verified: true` in `config/skip_gates.yaml` | REQUIRES SELORM |
| V6 | Year window and failing years make sense | `results/audit/window.json`, `tables/T_audit_years.csv` | PENDING REAL-DATA RUN |
| V7 | Weighted prevalence for 2023 national any-attempt is close to CDC's published estimate | `tables/T_prevalence.csv` (S_NAT population) vs MMWR 2023 | PENDING REAL-DATA RUN |
| V8 | Spot-check 3 surveys where an item is coded `NA_SITE` against that site's questionnaire | `results/audit/survey_item_missing_fraction.csv` | PENDING REAL-DATA RUN |
| V9 | Reproduce `S0_primary` on the MacBook from a clean clone and get identical split hashes | `results/splits/manifest.json` | PENDING REAL-DATA RUN |
| V10 | Every citation confirmed against the source | `docs/literature_review.md` tags | REQUIRES SELORM |
| V11 | Authorship of Dr. Merchant (and any co-author) discussed and agreed | Outside this repo | REQUIRES SELORM |
| V12 | Manuscript prose revised in the author's own voice | `manuscript/` | PENDING REAL-DATA RUN |
| V13 | BRFSS 2023 variable names and codes in `config/brfss.yaml` (ACE items, ADDEPEV3, `_STSTR`, `_PSU`, `_LLCPWT`, `_LCPWTV1`, demographics) | 2023 codebook | REQUIRES SELORM |
