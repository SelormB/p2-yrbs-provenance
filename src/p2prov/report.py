"""Figures, publication tables, and stats.json (the only source of numbers in the manuscript).

Palette: validated reference categorical slots 1-3 (blue, orange, aqua) and a single-hue
sequential blue ramp; text in neutral inks. Every figure carries a mode stamp.
"""
from __future__ import annotations

import glob
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from .methods import CONVENTIONAL, DIAGNOSTIC, PROVENANCE_AWARE  # noqa: E402

INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
FAMILY_COLOR = {"conventional": "#2a78d6", "provenance": "#eb6834", "diagnostic": "#1baf7a"}
SEQ = LinearSegmentedColormap.from_list("seqblue", ["#f4f8fd", "#9cc3ef", "#2a78d6", "#123f78"])
OUTCOME_LABEL = {"any_attempt": "Any past-year suicide attempt", "injurious_attempt": "Injurious suicide attempt"}


def family(m):
    return "provenance" if m in PROVENANCE_AWARE else ("diagnostic" if m in DIAGNOSTIC else "conventional")


def _style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)


def _stamp(fig, ctx):
    fig.text(0.99, -0.06, ctx.tag, ha="right", va="top", fontsize=7,
             color="#b3261e" if ctx.synthetic else INK2)


def _save(fig, ctx, name):
    for ext in ("png", "pdf"):
        fig.savefig(ctx.p(f"figures/{name}.{ext}"), dpi=300, bbox_inches="tight")
    plt.close(fig)


def _load(ctx, kind):
    fs = sorted(glob.glob(str(ctx.p(f"results/metrics/{kind}__*.csv"))))
    parts = []
    for f in fs:
        try:
            d = pd.read_csv(f)
        except pd.errors.EmptyDataError:
            continue
        stem = f.split(f"{kind}__")[1][:-4]
        o, s = stem.split("__")
        parts.append(d.assign(outcome=o, scenario=s) if "outcome" not in d else d)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def fig_provenance_map(ctx):
    """Shares computed over all state+district records per item x year (not summed across site types)."""
    prov = pd.read_parquet(ctx.p("processed/provenance.parquet"))
    raw = pd.read_parquet(ctx.p("interim/yrbs_raw.parquet"), columns=["row_id", "sitetype", "year"])
    df = prov.merge(raw, on="row_id")
    df = df[df["sitetype"].isin(["State", "District"])]
    items = [c for c in df.columns if c.startswith("prov__")]
    long = df.melt(id_vars=["year"], value_vars=items, var_name="item", value_name="code")
    long["item"] = long["item"].str.replace("prov__", "", regex=False)
    na = long.assign(v=long.code.isin(["NA_SITE", "NA_YEAR"])).groupby(["item", "year"])["v"].mean().unstack()
    un = long.assign(v=long.code.eq("NA_UNRES")).groupby(["item", "year"])["v"].mean().unstack()
    fig, axes = plt.subplots(1, 2, figsize=(9, 0.28 * len(na) + 1.6), sharey=True)
    for ax, M, title in [(axes[0], na, "Not asked (site omission or not on questionnaire)"),
                         (axes[1], un.reindex(na.index), "Missing, all records (unresolved)")]:
        im = ax.imshow(M.to_numpy(), aspect="auto", cmap=SEQ, vmin=0, vmax=1.0 if M is na else max(0.05, float(M.to_numpy().max())))
        ax.set_xticks(range(M.shape[1]), M.columns.astype(int), fontsize=8, color=INK2)
        ax.set_yticks(range(M.shape[0]), M.index, fontsize=8, color=INK2)
        ax.set_title(title, fontsize=9, color=INK, loc="left")
        for (i, j), v in np.ndenumerate(M.to_numpy()):
            ax.text(j, i, f"{v:.0%}" if v >= 0.005 else "", ha="center", va="center", fontsize=6,
                    color="white" if v > 0.6 * im.get_clim()[1] else INK)
        fig.colorbar(im, ax=ax, fraction=0.04, format=lambda x, _: f"{x:.0%}")
    fig.suptitle("Share of student records by missingness provenance, state and district surveys",
                 fontsize=10, color=INK, x=0.01, ha="left")
    _stamp(fig, ctx); _save(fig, ctx, "F1_provenance_map")


def fig_forest(ctx, met):
    p = met[(met.scenario == "S0_primary") & (met.metric == "auroc")]
    if p.empty:
        return
    wmode = "weighted" if (p.weighting == "weighted").any() else "unweighted"
    p = p[p.weighting == wmode]
    outs = [o for o in OUTCOME_LABEL if o in set(p.outcome)]
    fig, axes = plt.subplots(1, len(outs), figsize=(4.6 * len(outs), 4.2), sharey=True, squeeze=False)
    order = [m for m in CONVENTIONAL + PROVENANCE_AWARE + DIAGNOSTIC if m in set(p.method)]
    for ax, o in zip(axes[0], outs):
        q = p[p.outcome == o].set_index("method").reindex(order)
        yy = np.arange(len(order))[::-1]
        for yi, (m, r) in zip(yy, q.iterrows()):
            c = FAMILY_COLOR[family(m)]
            ax.plot([r.lo, r.hi], [yi, yi], color=c, lw=2, solid_capstyle="round")
            ax.plot(r.estimate, yi, "o", ms=8, color=c, mec="white", mew=2)
        ax.set_yticks(yy, order); ax.set_title(OUTCOME_LABEL[o], fontsize=9, loc="left", color=INK)
        ax.set_xlabel(f"AUROC ({wmode}, 95% design-bootstrap CI)", fontsize=8, color=INK2); _style(ax)
    handles = [plt.Line2D([], [], marker="o", ls="", color=c, label=k) for k, c in FAMILY_COLOR.items()]
    fig.legend(handles=handles, loc="lower left", ncol=3, frameon=False, fontsize=8, bbox_to_anchor=(0.01, -0.10))
    _stamp(fig, ctx); _save(fig, ctx, "F2_auroc_primary")


def fig_contrasts(ctx, con):
    c = con[(con.metric == "auroc") & (con.contrast.isin(["PROV_LR - MIND_LR", "PATTERN_LR - MEAN_LR",
                                                          "PROV_HGB - HGB_NATIVE"]))]
    if c.empty:
        return
    wmode = "weighted" if (c.weighting == "weighted").any() else "unweighted"
    c = c[c.weighting == wmode]
    outs = [o for o in OUTCOME_LABEL if o in set(c.outcome)]
    scen = sorted(c.scenario.unique(), key=lambda s: (s != "S0_primary", s))
    contrasts = ["PROV_LR - MIND_LR", "PATTERN_LR - MEAN_LR", "PROV_HGB - HGB_NATIVE"]
    cols = dict(zip(contrasts, ["#2a78d6", "#eb6834", "#1baf7a"]))
    fig, axes = plt.subplots(1, len(outs), figsize=(4.8 * len(outs), 0.42 * len(scen) + 1.5), sharey=True, squeeze=False)
    for ax, o in zip(axes[0], outs):
        base = np.arange(len(scen))[::-1]
        for k, ct in enumerate(contrasts):
            q = c[(c.outcome == o) & (c.contrast == ct)].set_index("scenario").reindex(scen)
            yy = base + (k - 1) * 0.22
            ax.hlines(yy, q.lo, q.hi, color=cols[ct], lw=2)
            ax.plot(q["diff"], yy, "o", ms=6, color=cols[ct], mec="white", mew=1.5, label=ct)
        ax.axvline(0, color=INK2, lw=0.8)
        ax.set_yticks(base, scen); ax.set_title(OUTCOME_LABEL[o], fontsize=9, loc="left", color=INK)
        ax.set_xlabel(f"Difference in AUROC ({wmode}), paired 95% CI", fontsize=8, color=INK2); _style(ax)
    axes[0][0].legend(frameon=False, fontsize=7, loc="lower left", bbox_to_anchor=(0, -0.35), ncol=3)
    _stamp(fig, ctx); _save(fig, ctx, "F3_contrasts_by_scenario")


def fig_calibration(ctx, cal):
    p = cal[(cal.scenario == "S0_primary") & cal.method.isin(["MIND_LR", "PROV_LR", "PATTERN_LR"])]
    if p.empty:
        return
    wmode = "weighted" if (p.weighting == "weighted").any() else "unweighted"
    p = p[p.weighting == wmode]
    outs = [o for o in OUTCOME_LABEL if o in set(p.outcome)]
    cols = {"MIND_LR": "#2a78d6", "PROV_LR": "#eb6834", "PATTERN_LR": "#1baf7a"}
    fig, axes = plt.subplots(1, len(outs), figsize=(4.2 * len(outs), 4), squeeze=False)
    for ax, o in zip(axes[0], outs):
        q = p[p.outcome == o]
        mx = float(max(q.mean_pred.max(), q.obs_rate.max())) * 1.05
        ax.plot([0, mx], [0, mx], color=INK2, lw=0.8, ls="--")
        for m, g in q.groupby("method"):
            ax.plot(g.mean_pred, g.obs_rate, "-o", color=cols[m], lw=2, ms=5, mec="white", label=m)
        ax.set_xlabel("Mean predicted risk (decile)", fontsize=8, color=INK2)
        ax.set_ylabel("Observed proportion", fontsize=8, color=INK2)
        ax.set_title(OUTCOME_LABEL[o], fontsize=9, loc="left", color=INK); _style(ax)
        ax.legend(frameon=False, fontsize=7)
    _stamp(fig, ctx); _save(fig, ctx, "F4_calibration_primary")


def tables(ctx, met, con, sub):
    if not met.empty:
        keep = ["auroc", "pr_auc", "brier", "cal_intercept", "cal_slope", "prevalence",
                "sens80_sensitivity", "sens80_specificity", "sens80_ppv", "sens80_npv",
                "top10_sensitivity", "top10_ppv"]
        t = met[(met.scenario == "S0_primary") & met.metric.isin(keep)].copy()
        t["value"] = t.apply(lambda r: f"{r.estimate:.3f} ({r.lo:.3f}–{r.hi:.3f})", axis=1)
        t.pivot_table(index=["outcome", "weighting", "method"], columns="metric", values="value",
                      aggfunc="first").reindex(columns=[k for k in keep if k in set(t.metric)]).to_csv(
            ctx.p("tables/T2_performance_primary.csv"))
        met.to_csv(ctx.p("tables/S_all_metrics_long.csv"), index=False)
    if not con.empty:
        con.to_csv(ctx.p("tables/T3_contrasts_all_scenarios.csv"), index=False)
    if not sub.empty:
        sub.to_csv(ctx.p("tables/T4_subgroups_all.csv"), index=False)


def stats_json(ctx, met, con):
    s = {"mode": "SYNTHETIC" if ctx.synthetic else "REAL", "verified_by_author": False}
    try:
        s["window"] = json.loads(ctx.p("results/audit/window.json").read_text())["years"]
        prev = pd.read_csv(ctx.p("tables/T_prevalence.csv"))
        for (o, pop), g in prev.groupby(["outcome", "population"]):
            s[f"prev_{o}_{pop}_n"] = int(g.n.sum()); s[f"prev_{o}_{pop}_events"] = int(g.events.sum())
            s[f"prev_{o}_{pop}_unweighted"] = float(g.events.sum() / g.n.sum())
    except FileNotFoundError:
        pass
    p = met[(met.scenario == "S0_primary")] if not met.empty else met
    for r in p.itertuples():
        s[f"{r.outcome}.{r.method}.{r.weighting}.{r.metric}"] = [r.estimate, r.lo, r.hi]
    for r in con.itertuples() if not con.empty else []:
        s[f"contrast.{r.outcome}.{r.scenario}.{r.contrast}.{r.weighting}.{r.metric}"] = [r.diff, r.lo, r.hi]
    ctx.p("results/stats.json").write_text(json.dumps(s, indent=1, default=float))
    return s


def build(ctx):
    met, con, sub, cal = (_load(ctx, k) for k in ["metrics", "contrasts", "subgroups", "calibration"])
    if ctx.p("tables/T_provenance_profile.csv").exists():
        fig_provenance_map(ctx)
    if not met.empty:
        fig_forest(ctx, met)
    if not con.empty:
        fig_contrasts(ctx, con)
    if not cal.empty:
        fig_calibration(ctx, cal)
    tables(ctx, met, con, sub)
    stats_json(ctx, met, con)
