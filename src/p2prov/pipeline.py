"""Stage functions called by scripts/NN_*.py. Each stage reads and writes files only."""
from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from . import audit as A
from . import harmonize as H
from . import io as IO
from . import metrics as M
from . import provenance as PV
from . import splits as SP
from .methods import BLOCKED, METHODS, PRIMARY_CONTRASTS, BlockedMethodError, Spec
from .scenarios import SCENARIOS

log = logging.getLogger("p2prov")
ROOT = Path(__file__).resolve().parents[2]


# ----------------------------------------------------------------------------- utilities
def load_config(path: Path | None = None) -> dict:
    cfg = yaml.safe_load((path or ROOT / "config/project.yaml").read_text())
    return cfg


class Ctx:
    """Run context: paths, mode (real vs SYNTHETIC), and run log."""

    def __init__(self, cfg: dict, raw_dir: Path, out_root: Path, synthetic: bool, dev: bool = False):
        self.cfg, self.raw, self.out, self.synthetic, self.dev = cfg, Path(raw_dir), Path(out_root), synthetic, dev
        for sub in ["interim", "processed", "results/audit", "results/splits", "results/preds",
                    "results/metrics", "figures", "tables", "logs"]:
            (self.out / sub).mkdir(parents=True, exist_ok=True)
        stamp = {"mode": "SYNTHETIC" if synthetic else "REAL", "dev": dev}
        (self.out / "RUN_MODE.json").write_text(json.dumps(stamp))

    @property
    def tag(self) -> str:
        return "SYNTHETIC — NOT A SCIENTIFIC RESULT" if self.synthetic else "DRAFT — UNVERIFIED"

    def p(self, rel: str) -> Path:
        return self.out / rel


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_provenance_log(ctx: Ctx):
    rows = []
    files = ctx.cfg["yrbs"]["data_files"] + [ctx.cfg["yrbs"]["sas_input_program"]]
    for fn in files:
        p = ctx.raw / fn
        if p.exists():
            rows.append({"file": fn, "bytes": p.stat().st_size, "sha256": sha256(p),
                         "source_url": f"{ctx.cfg['yrbs']['base_url']}/{fn}",
                         "synthetic": ctx.synthetic})
    pd.DataFrame(rows).to_csv(ctx.p("results/audit/data_provenance.csv"), index=False)


# ----------------------------------------------------------------------------- stage 01
def stage_resolve(ctx: Ctx) -> pd.DataFrame:
    y = ctx.cfg["yrbs"]
    text = (ctx.raw / y["sas_input_program"]).read_text(errors="replace")
    labels = IO.parse_sas_labels(text)
    fmt = ctx.raw / y["sas_format_program"]
    if fmt.exists():
        labels.update({k: v for k, v in IO.parse_sas_labels(fmt.read_text(errors="replace")).items()
                       if k not in labels})
    vm = H.resolve_concepts(labels, y["predictor_concepts"])
    override = ROOT / "config/variable_map.yaml"
    if override.exists() and not ctx.synthetic:
        ov = yaml.safe_load(override.read_text()) or {}
        for c, v in ov.items():
            vm.loc[vm.concept == c, ["matches", "n_matches", "status"]] = [v, 1, "AUTHOR_SET"]
    vm.to_csv(ctx.p("results/audit/variable_map.csv"), index=False)
    pd.Series(labels).rename("label").to_csv(ctx.p("results/audit/sas_labels.csv"))
    return vm


def resolved_items(ctx: Ctx) -> dict[str, str]:
    vm = pd.read_csv(ctx.p("results/audit/variable_map.csv"))
    ok = vm[vm.status.isin(["OK", "AUTHOR_SET"])]
    dropped = vm[~vm.status.isin(["OK", "AUTHOR_SET"])]
    if len(dropped):
        log.warning("Concepts needing author review (excluded until set in config/variable_map.yaml): %s",
                    list(dropped.concept))
    return dict(zip(ok.concept, ok.matches))


# ----------------------------------------------------------------------------- stage 02
def stage_ingest(ctx: Ctx) -> pd.DataFrame:
    y = ctx.cfg["yrbs"]
    d = y["design"]
    items = list(resolved_items(ctx).values())
    extra = [g["gate"] for g in skip_gates(ctx)] + [g["dependent"] for g in skip_gates(ctx)]
    extra += [v["raw"] for v in y.get("not_applicable", {}).values()]
    sas_fields = IO.parse_sas_layout((ctx.raw / y["sas_input_program"]).read_text(errors="replace"))
    have = {f.name for f in sas_fields}
    extra = [c for c in extra if c in have]  # optional helper columns
    cols = sorted(set(list(d.values()) + y["demographic_vars"] + y["proximal_items"] + items + extra +
                      [o["raw_var"] for o in y["outcomes"].values()]))
    absent = [c for c in cols if c not in have]
    if absent:
        raise KeyError(f"Variables not in CDC layout: {absent}. Check config.")
    df = IO.read_sadc(ctx.raw, y["data_files"], y["sas_input_program"], usecols=cols,
                      years=y["candidate_years"])
    df.to_parquet(ctx.p("interim/yrbs_raw.parquet"), index=False)
    write_provenance_log(ctx)
    return df


def skip_gates(ctx: Ctx) -> list[dict]:
    p = ROOT / ("config/skip_gates_synthetic.yaml" if ctx.synthetic else "config/skip_gates.yaml")
    if not p.exists():
        return []
    return [g for g in (yaml.safe_load(p.read_text()) or {}).get("gates", []) if g.get("verified") or ctx.synthetic]


# ----------------------------------------------------------------------------- stage 03
def stage_audit_years(ctx: Ctx) -> dict:
    y = ctx.cfg["yrbs"]; d = y["design"]
    df = pd.read_parquet(ctx.p("interim/yrbs_raw.parquet"))
    df = df[df[d["year"]].isin(y["candidate_years"])]
    items = list(resolved_items(ctx).values())
    outs = [o["raw_var"] for o in y["outcomes"].values()]
    aud = A.year_audit(df, items, outs, d)
    win = A.choose_window(aud, outs)
    win["candidate_years"] = y["candidate_years"]
    (ctx.p("results/audit/window.json")).write_text(json.dumps(win, indent=2, default=float))
    pd.DataFrame(win["audit"]).to_csv(ctx.p("tables/T_audit_years.csv"), index=False)
    return win


# ----------------------------------------------------------------------------- stage 04
def stage_provenance(ctx: Ctx, absent_threshold: float = 1.0) -> pd.DataFrame:
    y = ctx.cfg["yrbs"]; d = y["design"]
    df = pd.read_parquet(ctx.p("interim/yrbs_raw.parquet"))
    df = df[df[d["year"]].isin(y["candidate_years"])].reset_index(drop=True)
    items = list(resolved_items(ctx).values()) + y["proximal_items"]
    prov = PV.label_provenance(df, items, d["site"], d["year"], absent_threshold=absent_threshold)
    for it, rule in y.get("not_applicable", {}).items():
        if it in prov and rule["raw"] in df:
            na = df[it].isna() & df[rule["raw"]].isin(rule["codes"])
            prov.loc[na, it] = PV.OBS_NONSUB
    suffix = "" if absent_threshold == 1.0 else f"_thr{int(absent_threshold*100)}"
    prov.add_prefix("prov__").assign(row_id=df["row_id"]).to_parquet(
        ctx.p(f"processed/provenance{suffix}.parquet"), index=False)
    if suffix:
        return prov
    prof = PV.provenance_profile(prov, df[[d["site_type"], d["year"]]])
    prof.to_csv(ctx.p("tables/T_provenance_profile.csv"), index=False)
    PV.provenance_profile(prov).to_csv(ctx.p("tables/T_provenance_overall.csv"), index=False)
    av = PV.survey_availability(df, items, d["site"], d["year"])
    av["frac_missing"].to_csv(ctx.p("results/audit/survey_item_missing_fraction.csv"))
    # skip-consistency descriptives (not a missing code)
    rows = []
    for g in skip_gates(ctx):
        f = PV.skip_consistent_flag(df, g["gate"], g["gate_no_codes"], g["dependent"], g["implied_code"])
        for (yr, st), sub in df.assign(f=f).groupby([d["year"], d["site_type"]]):
            rows.append({"gate": g["gate"], "dependent": g["dependent"], "year": yr, "site_type": st,
                         "share_skip_consistent": float(sub["f"].mean()),
                         "dependent_missing_when_gate_no": float(sub.loc[sub[g["gate"]].isin(g["gate_no_codes"]),
                                                                        g["dependent"]].isna().mean())})
    pd.DataFrame(rows).to_csv(ctx.p("tables/T_skip_consistency.csv"), index=False)
    # outcome-pair consistency: missing q30 among q29 'did not attempt'
    oc = y["outcomes"]
    a, b = oc["any_attempt"]["raw_var"], oc["injurious_attempt"]["raw_var"]
    pair = df.groupby([d["year"], d["site_type"]]).apply(lambda s: pd.Series({
        "n": len(s), f"{a}_missing": s[a].isna().mean(), f"{b}_missing": s[b].isna().mean(),
        f"{b}_missing_given_{a}_none": s.loc[s[a] == 1, b].isna().mean(),
        f"{b}_missing_given_{a}_any": s.loc[s[a] > 1, b].isna().mean()}), include_groups=False).reset_index()
    pair.to_csv(ctx.p("tables/T_outcome_pair_missingness.csv"), index=False)
    return prov


# ----------------------------------------------------------------------------- stage 05
def outcome_pool(ctx: Ctx, outcome: str) -> pd.DataFrame:
    """All candidate-year records with a valid outcome, any population, any weighting (split pool)."""
    y = ctx.cfg["yrbs"]
    df = pd.read_parquet(ctx.p("interim/yrbs_raw.parquet"))
    pool, _ = H.build_cohort(df, ctx.cfg, y["candidate_years"], outcome, population="all", require_weight=False)
    return pool


def stage_splits(ctx: Ctx) -> dict:
    y = ctx.cfg["yrbs"]; d = y["design"]; seed = ctx.cfg["project"]["seed"]
    out = {}
    for outcome in y["outcomes"]:
        pool = outcome_pool(ctx, outcome)
        ph = SP.load_phmissbench_split(ROOT / ctx.cfg["splits"]["phmissbench_split_file"], pool["row_id"])
        structures = {
            "within_survey": (ph if ph is not None else SP.within_survey_split(pool, seed)),
            "leave_sites_out": SP.leave_sites_out_split(pool, d["site"], seed),
            "temporal_last_year": SP.temporal_split(pool, d["year"], seed),
        }
        for name, s in structures.items():
            meta = {"outcome": outcome, "structure": name, "seed": seed,
                    "source": "PH-MissBench" if (name == "within_survey" and ph is not None) else "P2-internal",
                    "synthetic": ctx.synthetic}
            h = SP.freeze(s, pool["row_id"], ctx.p(f"results/splits/{outcome}__{name}.parquet"), meta)
            out[f"{outcome}__{name}"] = {"sha256": h, **meta,
                                         "counts": s.value_counts().to_dict()}
    ctx.p("results/splits/manifest.json").write_text(json.dumps(out, indent=2))
    return out


# ----------------------------------------------------------------------------- stage 06
def _frame(df, items, prov, ctx, demo):
    d = ctx.cfg["yrbs"]["design"]
    X = df[items].replace({1: 1.0, 2: 0.0}).astype(float)  # CDC QN coding 1 = yes, 2 = no  [VERIFY V4]
    X = X.where(X.isin([0.0, 1.0]))
    w = df[d["weight"]].astype(float).to_numpy()
    return {"X": X.reset_index(drop=True), "D": df[demo].reset_index(drop=True),
            "P": prov.reset_index(drop=True), "S": df[[d["site"], d["year"]]].reset_index(drop=True),
            "y": df["y"].to_numpy().astype(int), "w": w,
            "row_id": df["row_id"].to_numpy(), "meta": df.reset_index(drop=True)}


def _subset(F, mask):
    m = np.asarray(mask)
    return {k: (v[m].reset_index(drop=True) if isinstance(v, pd.DataFrame) else v[m]) for k, v in F.items()}


def scenario_data(ctx: Ctx, outcome: str, scen: str):
    cfg, y = ctx.cfg, ctx.cfg["yrbs"]; d = y["design"]; S = SCENARIOS[scen]
    win = json.loads(ctx.p("results/audit/window.json").read_text())
    years = win["years"]
    if not years:
        raise RuntimeError("Audited window is empty; see results/audit/window.json")
    years = [yr for yr in years if yr not in S.get("drop_years", [])]
    if "only_years" in S:
        years = S["only_years"]
    df = pd.read_parquet(ctx.p("interim/yrbs_raw.parquet"))
    coh, flow = H.build_cohort(df, cfg, years, outcome, population=S.get("population", "site_level"),
                               require_weight=S.get("require_weight", True))
    thr = S.get("absent_threshold", 1.0)
    pfile = "processed/provenance.parquet" if thr == 1.0 else f"processed/provenance_thr{int(thr*100)}.parquet"
    if not ctx.p(pfile).exists():
        stage_provenance(ctx, absent_threshold=thr)
    prov = pd.read_parquet(ctx.p(pfile)).set_index("row_id").reindex(coh["row_id"])
    items = list(resolved_items(ctx).values())
    if S.get("add_proximal"):
        items += [i for i in y["proximal_items"] if i in coh.columns]
    if "drop_absent_items_over" in S:
        Pf = prov[[f"prov__{i}" for i in items]]
        surv_absent = Pf.isin([PV.NA_SITE, PV.NA_YEAR]).groupby(coh["survey_id"].to_numpy()).all().mean()
        items = [i for i in items if surv_absent[f"prov__{i}"] <= S["drop_absent_items_over"]]
    P = prov[[f"prov__{i}" for i in items]].copy()
    P.columns = items
    struct = {"leave_sites_out": "leave_sites_out", "temporal_last_year": "temporal_last_year"}.get(
        S.get("split", ""), "within_survey")
    sp = pd.read_parquet(ctx.p(f"results/splits/{outcome}__{struct}.parquet")).set_index("row_id")["split"]
    split = coh["row_id"].map(sp).to_numpy()
    F = _frame(coh, items, P, ctx, y["demographic_vars"])
    return F, split, flow, items


def stage_fit(ctx: Ctx, outcome: str, scen: str, methods: list[str] | None = None, force=False) -> pd.DataFrame:
    S = SCENARIOS[scen]
    out_path = ctx.p(f"results/preds/{outcome}__{scen}.parquet")
    if out_path.exists() and not force:
        log.info("checkpoint exists, skipping fit: %s", out_path)
        return pd.read_parquet(out_path)
    F, split, flow, items = scenario_data(ctx, outcome, scen)
    flow.to_csv(ctx.p(f"results/metrics/flow__{outcome}__{scen}.csv"), index=False)
    spec = Spec(use_weights_in_training=S.get("train_weights", False), add_site_year=S.get("add_site_year", False))
    seed = ctx.cfg["project"]["seed"]
    tr = _subset(F, split == "train")
    if S.get("require_weight", True) is False:
        tr["w"] = np.ones(len(tr["y"]))
    names = methods or list(METHODS)
    if S.get("split") == "leave_sites_out":
        names = [n for n in names if n != "STRUCT_ONLY"]  # unseen sites: site dummies undefined
    recs, status = [], []
    ev = _subset(F, np.isin(split, ["valid", "test"]))
    for name in names:
        t0 = time.time()
        try:
            m = METHODS[name](spec, seed).fit(tr)
            p = m.predict_proba(ev)
            recs.append(pd.DataFrame({"row_id": ev["row_id"], "split": split[np.isin(split, ["valid", "test"])],
                                      "method": name, "p": p}))
            status.append({"method": name, "status": "OK", "seconds": round(time.time() - t0, 1)})
        except Exception as e:  # recorded, never silently ignored
            log.exception("method %s failed", name)
            status.append({"method": name, "status": f"FAILED: {e}", "seconds": round(time.time() - t0, 1)})
    for name, cls in BLOCKED.items():
        try:
            cls(spec, seed).fit(tr)
        except BlockedMethodError as e:
            status.append({"method": name, "status": str(e), "seconds": 0})
    preds = pd.concat(recs, ignore_index=True)
    preds.to_parquet(out_path, index=False)
    meta = {"outcome": outcome, "scenario": scen, "items": items, "n_train": int(len(tr["y"])),
            "events_train": int(tr["y"].sum()), "split_counts": pd.Series(split).value_counts().to_dict(),
            "methods": status, "mode": "SYNTHETIC" if ctx.synthetic else "REAL"}
    ctx.p(f"results/metrics/fitmeta__{outcome}__{scen}.json").write_text(json.dumps(meta, indent=2, default=str))
    return preds


# ----------------------------------------------------------------------------- stage 07
def stage_evaluate(ctx: Ctx, outcome: str, scen: str) -> pd.DataFrame:
    S = SCENARIOS[scen]
    F, split, _, _ = scenario_data(ctx, outcome, scen)
    preds = pd.read_parquet(ctx.p(f"results/preds/{outcome}__{scen}.parquet"))
    meta = F["meta"].set_index("row_id")
    ev = ctx.cfg["evaluation"]
    reps = ev["bootstrap_reps_dev"] if ctx.dev else ev["bootstrap_reps"]
    seed = ctx.cfg["project"]["seed"]
    weighted_ok = S.get("require_weight", True)
    rows, cal_rows, sub_rows, thr_rows = [], [], [], []
    test_ids = preds.loc[preds.split == "test", "row_id"].unique()
    tm = meta.loc[test_ids]
    # Variance strata = survey (site x year), clusters = PSU. Using the survey's own strata left many
    # test-set strata with a single PSU (zero variance contribution) because only 20% of PSUs per survey
    # are in the test split; collapsing to survey-level strata is conservative. (DECISIONS 2026-10-10)
    boot_strata, boot_psu = tm["survey_id"].to_numpy(), tm["design_psu"].to_numpy()
    st = pd.DataFrame({"h": tm["design_stratum"].to_numpy(), "c": boot_psu}).drop_duplicates()
    k = st.groupby("h").c.nunique()
    sv = pd.DataFrame({"h": boot_strata, "c": boot_psu}).drop_duplicates().groupby("h").c.nunique()
    diag = {"test_rows": int(len(tm)), "design_strata": int(len(k)), "design_strata_single_psu": int((k == 1).sum()),
            "survey_strata": int(len(sv)), "survey_strata_single_psu": int((sv == 1).sum()),
            "test_psus": int(st.c.nunique())}
    ctx.p(f"results/metrics/bootdiag__{outcome}__{scen}.json").write_text(json.dumps(diag, indent=2))
    P = {}
    for name, g in preds.groupby("method"):
        va, te = g[g.split == "valid"].set_index("row_id"), g[g.split == "test"].set_index("row_id").reindex(test_ids)
        P[name] = te["p"].to_numpy()
        yv, wv = meta.loc[va.index, "y"].to_numpy(), meta.loc[va.index, "weight"].to_numpy()
        okv = ~np.isnan(va["p"].to_numpy())
        wv_use = wv[okv] if weighted_ok else None
        thrs = {t["name"]: M.choose_threshold(yv[okv], va["p"].to_numpy()[okv], t["rule"], t["value"], wv_use)
                for t in ev["thresholds"]}
        for k, v in thrs.items():
            thr_rows.append({"method": name, "threshold": k, "value": v, "chosen_on": "validation"})
        yt, wt = tm["y"].to_numpy(), tm["weight"].to_numpy()
        ok = ~np.isnan(P[name])
        for wmode in (["unweighted", "weighted"] if weighted_ok else ["unweighted"]):
            base_w = wt[ok] if wmode == "weighted" else None
            boot = M.DesignBootstrap(boot_strata[ok], boot_psu[ok], seed)
            fn = lambda yy, pp, ww: M.all_metrics(yy, pp, ww, thrs)
            res = M.bootstrap_ci(fn, yt[ok], P[name][ok], base_w, boot, reps)
            for k, (e, lo, hi) in res.items():
                rows.append({"outcome": outcome, "scenario": scen, "method": name, "weighting": wmode,
                             "metric": k, "estimate": e, "lo": lo, "hi": hi, "coverage": float(ok.mean()),
                             "n_test": int(ok.sum()), "events_test": int(yt[ok].sum())})
            cc = M.calibration_curve(yt[ok], P[name][ok], base_w, ev["calibration_bins"])
            cal_rows.append(cc.assign(method=name, weighting=wmode))
        # subgroups (weighted when available), events threshold enforced
        wsub = wt if weighted_ok else np.ones(len(wt))
        for var in ev["subgroups"]:
            col = {"site_type": "sitetype", "year": "year"}.get(var, var)
            if col not in tm:
                continue
            for lev, idx in tm.groupby(col).indices.items():
                idx = idx[ok[idx]]
                if yt[idx].sum() < ev["min_subgroup_events"] or yt[idx].sum() == len(idx):
                    continue
                sb = M.DesignBootstrap(boot_strata[idx], boot_psu[idx], seed)
                e, lo, hi = M.bootstrap_ci(M.auroc, yt[idx], P[name][idx], wsub[idx], sb, max(20, reps // 5))
                a_, s_ = M.calibration_intercept_slope(yt[idx], P[name][idx], wsub[idx])
                sub_rows.append({"method": name, "subgroup": var, "level": lev, "n": len(idx),
                                 "events": int(yt[idx].sum()), "auroc": e, "auroc_lo": lo, "auroc_hi": hi,
                                 "cal_intercept": a_, "cal_slope": s_})
    # paired contrasts on rows every method covers
    con = []
    yt, wt = tm["y"].to_numpy(), tm["weight"].to_numpy()
    for a, b in PRIMARY_CONTRASTS + [("PROV_LR", "STRUCT_ONLY"), ("MIND_LR", "STRUCT_ONLY")]:
        if a not in P or b not in P:
            continue
        ok = ~np.isnan(P[a]) & ~np.isnan(P[b])
        boot = M.DesignBootstrap(boot_strata[ok], boot_psu[ok], seed + 1)
        for mname, fn in [("auroc", M.auroc), ("pr_auc", M.average_precision), ("brier", M.brier)]:
            for wmode in (["unweighted", "weighted"] if weighted_ok else ["unweighted"]):
                bw = wt[ok] if wmode == "weighted" else None
                e, lo, hi = M.paired_difference_ci(fn, yt[ok], P[a][ok], P[b][ok], bw, boot, reps)
                con.append({"outcome": outcome, "scenario": scen, "contrast": f"{a} - {b}", "metric": mname,
                            "weighting": wmode, "diff": e, "lo": lo, "hi": hi})
    res = pd.DataFrame(rows)
    base = f"{outcome}__{scen}"
    res.to_csv(ctx.p(f"results/metrics/metrics__{base}.csv"), index=False)
    pd.concat(cal_rows).to_csv(ctx.p(f"results/metrics/calibration__{base}.csv"), index=False)
    pd.DataFrame(sub_rows).to_csv(ctx.p(f"results/metrics/subgroups__{base}.csv"), index=False)
    pd.DataFrame(thr_rows).to_csv(ctx.p(f"results/metrics/thresholds__{base}.csv"), index=False)
    pd.DataFrame(con).to_csv(ctx.p(f"results/metrics/contrasts__{base}.csv"), index=False)
    return res


# ----------------------------------------------------------------------------- stage 08 (descriptives)
def stage_descriptives(ctx: Ctx) -> pd.DataFrame:
    """Design-based outcome prevalence per year x site type, in the primary cohort definition."""
    y = ctx.cfg["yrbs"]
    win = json.loads(ctx.p("results/audit/window.json").read_text())
    df = pd.read_parquet(ctx.p("interim/yrbs_raw.parquet"))
    rows = []
    for outcome in y["outcomes"]:
        for pop in ["site_level", "national"]:
            coh, flow = H.build_cohort(df, ctx.cfg, win["years"], outcome, population=pop)
            flow.to_csv(ctx.p(f"tables/T_flow__{outcome}__{pop}.csv"), index=False)
            for yr, g in coh.groupby("year"):
                e, se, lo, hi = M.weighted_prevalence(g["y"], g["weight"], g["design_stratum"], g["design_psu"])
                rows.append({"outcome": outcome, "population": pop, "year": yr, "n": len(g),
                             "events": int(g["y"].sum()), "unweighted_prev": g["y"].mean(),
                             "weighted_prev": e, "se": se, "lo": lo, "hi": hi})
    t = pd.DataFrame(rows)
    t.to_csv(ctx.p("tables/T_prevalence.csv"), index=False)
    return t
