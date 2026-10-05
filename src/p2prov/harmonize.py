"""Variable resolution, harmonization, and cohort construction."""
from __future__ import annotations

import re

import numpy as np
import pandas as pd


def resolve_concepts(labels: dict[str, str], concepts: dict[str, str], prefix: str = "qn") -> pd.DataFrame:
    """Match predictor concepts to CDC QN variables by label regex.

    Returns one row per concept with the matched variable(s). Concepts that match zero or
    several variables are flagged; the author resolves them in config/variable_map.yaml.
    """
    rows = []
    for concept, pattern in concepts.items():
        rx = re.compile(pattern, re.I)
        hits = sorted(v for v, lab in labels.items() if v.startswith(prefix) and rx.search(lab))
        rows.append({"concept": concept, "pattern": pattern, "n_matches": len(hits),
                     "matches": ";".join(hits), "status": "OK" if len(hits) == 1 else "REVIEW",
                     "label": labels.get(hits[0], "") if len(hits) == 1 else ""})
    return pd.DataFrame(rows)


def make_outcome(series: pd.Series, positive: list, valid: list) -> pd.Series:
    y = pd.Series(np.nan, index=series.index)
    ok = series.isin(valid)
    y[ok] = series[ok].isin(positive).astype(float)
    return y


def add_design_ids(df: pd.DataFrame, d: dict) -> pd.DataFrame:
    """Make strata and PSUs unique across pooled surveys (site x year)."""
    out = df.copy()
    sy = out[d["site"]].astype(str) + "|" + out[d["year"]].astype(int).astype(str)
    out["survey_id"] = sy
    out["design_stratum"] = sy + "|" + out[d["stratum"]].astype("Int64").astype(str)
    out["design_psu"] = out["design_stratum"] + "|" + out[d["psu"]].astype("Int64").astype(str)
    return out


def build_cohort(df: pd.DataFrame, cfg: dict, years: list[int], outcome: str,
                 population: str = "site_level", require_weight: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply inclusion rules in a fixed order and return (cohort, flow table).

    population: 'site_level' (state + district surveys, primary), 'national', or 'all'.
    """
    d = cfg["yrbs"]["design"]
    oc = cfg["yrbs"]["outcomes"][outcome]
    flow = []

    def step(name, frame):
        flow.append({"step": name, "n": len(frame), "surveys": frame["survey_id"].nunique()
                     if "survey_id" in frame else np.nan})
        return frame

    x = add_design_ids(df, d)
    x = step("records in combined file", x)
    x = step(f"years in {years}", x[x[d["year"]].isin(years)])
    if population == "site_level":
        x = step("state and district surveys", x[x[d["site_type"]].isin(["State", "District"])])
    elif population == "national":
        x = step("national survey", x[x[d["site_type"]] == "National"])
    if require_weight:
        x = step("weighted (representative) surveys", x[x[d["weight"]].notna() & (x[d["weight"]] > 0)])
    asked = x.groupby("survey_id")[oc["raw_var"]].transform(lambda s: s.notna().any())
    x = step("survey asked the outcome item", x[asked])
    x = x.assign(y=make_outcome(x[oc["raw_var"]], oc["positive_codes"], oc["valid_codes"]))
    x = step("valid outcome response", x[x["y"].notna()])
    return x.reset_index(drop=True), pd.DataFrame(flow)
