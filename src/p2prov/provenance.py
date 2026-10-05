"""Missingness-provenance labelling for the YRBS combined data.

Each (record, item) cell receives exactly one provenance code. Codes are limited to
what can be identified from the RELEASED data; conceptual sources that cannot be
separated are deliberately pooled (see docs/taxonomy.md for the full mapping,
including the CDC statement that missing-because-not-on-questionnaire, nonresponse,
and edit-to-missing cannot be distinguished at the individual level in national data).

Codes
-----
OBS        observed substantive response
OBS_NONSUB observed non-substantive response (e.g. "I do not know what this question is asking")
NA_YEAR    item absent from every survey in that year (questionnaire-version absence)
NA_SITE    item absent from this site-year survey but present in others that year
NA_UNRES   missing inside a survey that asked the item: item nonresponse, CDC
           consistency edit set to missing, out-of-range edit, or (national file only)
           a student who received a site questionnaire lacking the item. Not separable.

Flag (not a missing code): SKIP_CONSISTENT marks an OBS value that equals the value CDC
assigns to appropriately skipped questions given the gate item. In electronically
administered surveys such cells may be skip-coded rather than answered; in paper
surveys they were answered. The released data do not say which.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

OBS, OBS_NONSUB, NA_YEAR, NA_SITE, NA_UNRES = "OBS", "OBS_NONSUB", "NA_YEAR", "NA_SITE", "NA_UNRES"
CODES = [OBS, OBS_NONSUB, NA_YEAR, NA_SITE, NA_UNRES]
MISSING_CODES = [NA_YEAR, NA_SITE, NA_UNRES]


def survey_availability(df: pd.DataFrame, items: list[str], site: str, year: str,
                        absent_threshold: float = 1.0) -> pd.DataFrame:
    """Per site-year survey: fraction missing for each item and whether it counts as not asked.

    An item is treated as not on a survey's questionnaire when its missing fraction in that
    survey is >= absent_threshold (primary 1.0; sensitivity analysis S-THR uses 0.95).
    """
    g = df.groupby([site, year])[items]
    frac = g.apply(lambda x: x.isna().mean())
    frac.columns = items
    absent = frac >= absent_threshold
    year_absent = absent.groupby(level=1).transform("all")
    out = pd.concat({"frac_missing": frac, "absent": absent, "year_absent": year_absent}, axis=1)
    return out


def label_provenance(df: pd.DataFrame, items: list[str], site: str, year: str,
                     nonsubstantive: dict[str, list] | None = None,
                     absent_threshold: float = 1.0) -> pd.DataFrame:
    """Return a DataFrame (same index as df) of provenance codes for each item."""
    nonsubstantive = nonsubstantive or {}
    avail = survey_availability(df, items, site, year, absent_threshold)
    keys = pd.MultiIndex.from_frame(df[[site, year]])
    prov = pd.DataFrame(index=df.index, columns=items, dtype=object)
    for it in items:
        absent = avail[("absent", it)].reindex(keys).to_numpy()
        yabsent = avail[("year_absent", it)].reindex(keys).to_numpy()
        isna = df[it].isna().to_numpy()
        code = np.where(~isna, OBS, NA_UNRES).astype(object)
        code[isna & absent & ~yabsent] = NA_SITE
        code[isna & yabsent] = NA_YEAR
        if it in nonsubstantive:
            code[(~isna) & df[it].isin(nonsubstantive[it]).to_numpy()] = OBS_NONSUB
        prov[it] = code
    return prov


def skip_consistent_flag(df: pd.DataFrame, gate: str, gate_no_codes: list,
                         dependent: str, implied_code) -> pd.Series:
    """True where gate says 'did not engage' and dependent holds the skip-implied value."""
    return df[gate].isin(gate_no_codes) & (df[dependent] == implied_code)


def provenance_profile(prov: pd.DataFrame, by: pd.DataFrame | None = None) -> pd.DataFrame:
    """Long table: share of each provenance code per item (optionally per group)."""
    long = prov.melt(var_name="item", value_name="code", ignore_index=False)
    if by is not None:
        long = long.join(by)
        keys = list(by.columns) + ["item"]
    else:
        keys = ["item"]
    tab = long.groupby(keys)["code"].value_counts(normalize=True).rename("share").reset_index()
    return tab
