"""Year-window audit: decide which cycles are pooled, using pre-stated rules (protocol 4)."""
from __future__ import annotations

import pandas as pd

from .provenance import survey_availability


def year_audit(df: pd.DataFrame, items: list[str], outcomes: list[str], d: dict) -> pd.DataFrame:
    site, year = d["site"], d["year"]
    avail = survey_availability(df, items + outcomes, site, year)
    surveys = avail.reset_index()
    rows = []
    for y, g in surveys.groupby(year):
        r = {"year": int(y), "n_surveys": len(g),
             "n_records": int((df[year] == y).sum())}
        for o in outcomes:
            r[f"{o}_asked_share"] = float((~g[("absent", o)]).mean())
        on_q = [it for it in items if not g[("year_absent", it)].all()]
        r["predictor_items_in_year"] = len(on_q)
        r["predictor_items_total"] = len(items)
        r["median_site_absence_share"] = float(g[[("absent", it) for it in items]].mean(axis=1).median())
        rows.append(r)
    return pd.DataFrame(rows)


def choose_window(audit: pd.DataFrame, outcomes: list[str], min_outcome_asked: float = 0.5,
                  min_item_share: float = 0.8) -> dict:
    """Return the longest contiguous run of cycles meeting all rules (latest run wins ties).

    Rules (protocol 4.2): each outcome item asked in >= 50% of that year's surveys (surveys
    that omit an outcome are excluded from that outcome's cohort anyway), and >= 80% of
    predictor concepts on that year's questionnaire. Years that fail are reported, not silently
    dropped. If no year qualifies the window is empty and downstream stages stop.
    """
    a = audit.sort_values("year").reset_index(drop=True)
    ok = (a["predictor_items_in_year"] / a["predictor_items_total"] >= min_item_share)
    for o in outcomes:
        ok &= a[f"{o}_asked_share"] >= min_outcome_asked
    a["meets_rules"] = ok
    best, cur = [], []
    for _, r in a.iterrows():
        cur = cur + [int(r["year"])] if r["meets_rules"] else []
        if len(cur) >= len(best):
            best = list(cur)
    return {"years": best, "audit": a.to_dict(orient="records"),
            "rules": {"min_outcome_asked": min_outcome_asked, "min_item_share": min_item_share}}
