"""BRFSS 2023 contrasting testbed: ACE-module information absence in an interviewer-administered survey.

Provenance classes for each ACE cell (contrast with YRBS, where these cannot be separated):

    OBS             substantive answer
    OBS_NA_STRUCT   answered "not applicable" (e.g. parents never married)  -> observed, not missing
    DK_REF          don't know / refused (BRFSS codes them explicitly; YRBS cannot)
    NA_STATE        state did not field the ACE module on any data set
    NA_VERSION      state fielded the module only on a split questionnaire version this respondent did not get
    NA_BREAKOFF     blank from this item to the end of the module after at least one answer
    NA_ITEM         other blank inside a fielded module

For modeling, codes are mapped onto the YRBS method interface:
NA_STATE, NA_VERSION -> NA_SITE (not asked); NA_BREAKOFF, NA_ITEM -> NA_UNRES;
DK_REF, OBS_NA_STRUCT -> OBS_NONSUB (value set to missing / not-applicable indicator).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from . import metrics as M
from . import splits as SP
from .methods import METHODS, Spec
from .provenance import NA_SITE, NA_UNRES, OBS, OBS_NONSUB

ROOT = Path(__file__).resolve().parents[2]
BCODES = ["OBS", "OBS_NA_STRUCT", "DK_REF", "NA_STATE", "NA_VERSION", "NA_BREAKOFF", "NA_ITEM"]
TO_METHOD_CODE = {"OBS": OBS, "OBS_NA_STRUCT": OBS_NONSUB, "DK_REF": OBS_NONSUB, "NA_STATE": NA_SITE,
                  "NA_VERSION": NA_SITE, "NA_BREAKOFF": NA_UNRES, "NA_ITEM": NA_UNRES}


def load_cfg() -> dict:
    return yaml.safe_load((ROOT / "config/brfss.yaml").read_text())


def read_xpt(path: Path) -> pd.DataFrame:
    df = pd.read_sas(path, format="xport", encoding="latin1")
    df.columns = [c.lower() for c in df.columns]
    return df


def module_states(df: pd.DataFrame, items: list[str], state: str) -> set:
    """States where any respondent has any non-blank ACE value (module fielded on this data set)."""
    any_ans = df[items].notna().any(axis=1)
    return set(df.loc[any_ans, state].unique())


def label_provenance(df: pd.DataFrame, cfg: dict, main_states: set, version_states: set) -> pd.DataFrame:
    items, st = cfg["ace_items"], cfg["design"]["state"]
    A = df[items]
    out = pd.DataFrame("NA_ITEM", index=df.index, columns=items, dtype=object)
    in_main = df[st].isin(main_states).to_numpy()
    in_version = df[st].isin(version_states).to_numpy() & ~in_main
    answered = A.notna().to_numpy()
    # breakoff: blanks after the last non-blank item in module order, given >= 1 answer
    last = np.where(answered.any(axis=1), answered.shape[1] - 1 - np.argmax(answered[:, ::-1], axis=1), -1)
    pos = np.arange(len(items))[None, :]
    breakoff = (~answered) & (pos > last[:, None]) & (last[:, None] >= 0)
    codes = np.where(answered, "OBS", np.where(breakoff, "NA_BREAKOFF", "NA_ITEM")).astype(object)
    for j, it in enumerate(items):
        v = A[it].to_numpy()
        codes[np.isin(v, cfg["dk_ref_codes"]), j] = "DK_REF"
        codes[np.isin(v, cfg.get("ace_not_applicable", {}).get(it, [])), j] = "OBS_NA_STRUCT"
    codes[~in_main & ~in_version, :] = "NA_STATE"
    codes[in_version, :] = "NA_VERSION"
    out[:] = codes
    return out


def ace_binary(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    X = pd.DataFrame(index=df.index)
    for it in cfg["ace_items"]:
        v = df[it]
        X[it] = np.where(v.isin(cfg["ace_yes"][it]), 1.0, np.where(v.isin(cfg["ace_no"][it]), 0.0, np.nan))
    return X


def build_frame(df: pd.DataFrame, cfg: dict, prov: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    d, oc = cfg["design"], cfg["outcome"]
    keep = df[oc["var"]].isin(oc["valid"]) & df[d["weight_main"]].notna()
    df, prov = df[keep].reset_index(drop=True), prov[keep].reset_index(drop=True)
    y = df[oc["var"]].isin(oc["positive"]).astype(int).to_numpy()
    df = df.assign(y=y, design_stratum=df[d["state"]].astype(str) + "|" + df[d["stratum"]].astype(str),
                   row_id=df.index.astype(str))
    df["design_psu"] = df["design_stratum"] + "|" + df[d["psu"]].astype(str)
    df["survey_id"] = df[d["state"]].astype(str)
    F = {"X": ace_binary(df, cfg), "D": df[cfg["demographics"]].astype(float),
         "P": prov.replace(TO_METHOD_CODE), "S": df[[d["state"]]].assign(year=2023),
         "y": y, "w": df[d["weight_main"]].to_numpy(float), "row_id": df["row_id"].to_numpy(), "meta": df}
    return F, prov


def run(raw: Path, out: Path, synthetic: bool = False, dev: bool = True, df: pd.DataFrame | None = None) -> dict:
    """Primary (within-state PSU split) and leave-states-out evaluation on the BRFSS main file."""
    cfg = load_cfg()
    d = cfg["design"]
    out = Path(out) / "results/brfss"
    out.mkdir(parents=True, exist_ok=True)
    if df is None:
        df = read_xpt(raw / "LLCP2023.XPT")
        v1 = read_xpt(raw / "LLCP23V1.XPT") if (raw / "LLCP23V1.XPT").exists() else None
    else:
        v1 = None
    items = cfg["ace_items"]
    main_states = module_states(df, items, d["state"])
    version_states = module_states(v1, items, d["state"]) - main_states if v1 is not None else set()
    prov = label_provenance(df, cfg, main_states, version_states)
    prov.apply(lambda c: c.value_counts(normalize=True)).T.to_csv(out / "T_brfss_provenance.csv")
    F, _ = build_frame(df, cfg, prov)
    summary = {"mode": "SYNTHETIC" if synthetic else "REAL", "n": int(len(F["y"])),
               "events": int(F["y"].sum()), "module_states_main": sorted(map(str, main_states)),
               "module_states_version_only": sorted(map(str, version_states))}
    e, se, lo, hi = M.weighted_prevalence(F["y"], F["w"], F["meta"]["design_stratum"], F["meta"]["design_psu"])
    summary["weighted_prevalence"] = [e, lo, hi]
    reps = 50 if dev else 1000
    rows = []
    structures = {"within_state": SP.within_survey_split(F["meta"], cfg["seed"]),
                  "leave_states_out": SP.leave_sites_out_split(F["meta"], d["state"], cfg["seed"])}
    for sname, split in structures.items():
        split = split.to_numpy()
        sub = lambda m: {k: (v[m].reset_index(drop=True) if isinstance(v, pd.DataFrame) else v[m])
                         for k, v in F.items()}
        tr, te = sub(split == "train"), sub(split == "test")
        boot = M.DesignBootstrap(te["meta"]["design_stratum"], te["meta"]["design_psu"], cfg["seed"])
        for name in ["MEAN_LR", "MIND_LR", "PROV_LR", "PATTERN_LR", "HGB_NATIVE", "PROV_HGB", "DEMO_LR"]:
            p = METHODS[name](Spec(), cfg["seed"]).fit(tr).predict_proba(te)
            ok = ~np.isnan(p)
            for metric, fn in [("auroc", M.auroc), ("brier", M.brier)]:
                est, l, h = M.bootstrap_ci(fn, te["y"][ok], p[ok], te["w"][ok],
                                           M.DesignBootstrap(te["meta"]["design_stratum"][ok],
                                                             te["meta"]["design_psu"][ok], cfg["seed"]), reps)
                rows.append({"structure": sname, "method": name, "metric": metric, "weighting": "weighted",
                             "estimate": est, "lo": l, "hi": h})
    pd.DataFrame(rows).to_csv(out / "metrics_brfss.csv", index=False)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=float))
    return summary


def synthetic_brfss(seed: int = 3, n_states: int = 12, n_per: int = 600) -> pd.DataFrame:
    """SYNTHETIC BRFSS-like frame for tests (not CDC data)."""
    cfg = load_cfg(); rng = np.random.default_rng(seed)
    rows = []
    for s in range(1, n_states + 1):
        lat = rng.normal(0, 1, n_per)
        df = pd.DataFrame({"_state": s, "_ststr": s * 10 + rng.integers(1, 4, n_per),
                           "_psu": rng.integers(1, 10**6, n_per), "_llcpwt": rng.gamma(3, 100, n_per),
                           "_ageg5yr": rng.integers(1, 14, n_per), "_sex": rng.integers(1, 3, n_per),
                           "_imprace": rng.integers(1, 7, n_per), "_educag": rng.integers(1, 5, n_per),
                           "_incomg1": rng.integers(1, 8, n_per)})
        for it in cfg["ace_items"]:
            yes = rng.random(n_per) < 1 / (1 + np.exp(-(-1.3 + 0.9 * lat)))
            yv, nv = cfg["ace_yes"][it][0], cfg["ace_no"][it][0]
            df[it] = np.where(yes, yv, nv).astype(float)
            df.loc[rng.random(n_per) < 0.02, it] = rng.choice(cfg["dk_ref_codes"])
            df.loc[rng.random(n_per) < 0.02, it] = np.nan
        brk = rng.random(n_per) < 0.02  # breakoff before the last 3 items
        df.loc[brk, cfg["ace_items"][-3:]] = np.nan
        if s > 6:  # states 7..12 did not field the module
            df[cfg["ace_items"]] = np.nan
        df["addepev3"] = np.where(rng.random(n_per) < 1 / (1 + np.exp(-(-1.6 + 0.8 * lat))), 1, 2)
        df.loc[rng.random(n_per) < 0.01, "addepev3"] = 9
        rows.append(df)
    return pd.concat(rows, ignore_index=True)
