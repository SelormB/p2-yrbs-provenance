"""Preprint figures in the PH-MissBench preprint style, drawn from the real-run result tables."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "fig"
OUT.mkdir(exist_ok=True)
BLUE, ORANGE, GREEN, GREY = "#2b7bd6", "#ee6a35", "#2a9d6f", "#9aa3ad"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": "#e6e6e6",
                     "grid.linewidth": 0.8, "axes.axisbelow": True, "axes.edgecolor": "#444"})

ITEM = {"qn12": "Weapon at school", "qn14": "Skipped school, unsafe", "qn16": "Physical fight",
        "qn19": "Forced sex", "qn22": "Physical dating violence", "qn24": "Bullied at school",
        "qn25": "Bullied electronically", "qn26": "Sad or hopeless", "qn27": "Seriously considered suicide",
        "qn28": "Made a suicide plan", "qn33": "Current cigarette use", "qn36": "Current vaping",
        "qn42": "Current alcohol use", "qn48": "Current marijuana use",
        "qn49": "Rx pain medicine misuse", "qn85": "8+ hours of sleep", "qn87": "Mostly A's or B's"}
PRED = ["qn12", "qn14", "qn16", "qn19", "qn22", "qn24", "qn25", "qn26", "qn33", "qn36", "qn42",
        "qn48", "qn49", "qn85", "qn87"]
SCEN = {"S0_primary": "Primary", "S_LSO": "Jurisdictions held out", "S_TEMP": "Latest cycle held out",
        "S_NAT": "National survey only", "S_NO2021": "Excluding 2021", "S_PRE2023": "Excluding 2023",
        "S_ONLY2023": "2023 only", "S_DROPABS": "Often-omitted items dropped",
        "S_THR95": "95% not-asked rule", "S_PROX": "Ideation and plan added",
        "S_FE": "Site and year effects added", "S_WTRAIN": "Weighted training"}
OUTC = {"any_attempt": "Any past-year suicide attempt", "injurious_attempt": "Injurious suicide attempt"}


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def fig1():
    p = pd.read_csv(ROOT / "tables/T_provenance_overall.csv")
    p = p[p["item"].isin(PRED)].pivot_table(index="item", columns="code", values="share", fill_value=0)
    cols = [("NA_SITE", "Not asked by the survey", BLUE), ("NA_YEAR", "Not on that year's questionnaire", GREY),
            ("NA_UNRES", "Missing where asked", ORANGE), ("OBS_NONSUB", "Not applicable (did not date)", GREEN)]
    p["tot"] = sum(p.get(c, 0) for c, _, _ in cols)
    p = p.sort_values("tot")
    fig, ax = plt.subplots(figsize=(6.6, 4.3))
    y = np.arange(len(p)); left = np.zeros(len(p))
    for c, lab, col in cols:
        v = p.get(c, pd.Series(0, index=p.index)).to_numpy() * 100
        ax.barh(y, v, left=left, color=col, height=0.62, label=lab)
        left += v
    for i, t in enumerate(p["tot"] * 100):
        ax.text(t + 0.6, i, f"{t:.1f}%", va="center", fontsize=7.2, color="#333")
    ax.set_yticks(y, [ITEM[i] for i in p.index])
    ax.set_xlabel("Share of student records with the item absent, 2015–2023 (%)")
    ax.set_xlim(0, max(p["tot"]) * 100 + 9)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right", frameon=False, fontsize=7.5)
    save(fig, "fig1_provenance")


def _parse(s):
    est, rest = s.split(" (")
    lo, hi = rest.rstrip(")").rsplit("–", 1)
    return float(est), float(lo), float(hi)


def fig2():
    t = pd.read_csv(ROOT / "tables/T2_performance_primary.csv")
    t = t[t.weighting == "weighted"]
    order = ["CC_LR", "MEAN_LR", "MIND_LR", "MICE_LR", "HGB_NATIVE", "PROV_LR", "PROV_HGB", "PATTERN_LR",
             "STRUCT_ONLY", "DEMO_LR"]
    col = {m: BLUE for m in order[:5]} | {m: ORANGE for m in order[5:8]} | {m: GREEN for m in order[8:]}
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.5), sharey=True)
    for ax, oc in zip(axes, OUTC):
        d = t[t.outcome == oc].set_index("method")
        for i, m in enumerate(order):
            e, lo, hi = _parse(d.loc[m, "auroc"])
            ax.plot([lo, hi], [i, i], color=col[m], lw=1.6)
            ax.plot(e, i, "o", color=col[m], ms=4.5, mec="white", mew=0.8)
        ax.set_title(OUTC[oc], fontsize=9, loc="left")
        ax.set_xlim(0.5, 0.88)
        ax.set_xlabel("Survey-weighted test AUROC (95% CI)")
        ax.grid(axis="y", visible=False)
    axes[0].set_yticks(range(len(order)), order)
    axes[0].invert_yaxis()
    h = [plt.Line2D([], [], color=c, marker="o", lw=1.6, label=l) for c, l in
         [(BLUE, "Conventional"), (ORANGE, "Provenance- or structure-aware"), (GREEN, "Diagnostic")]]
    fig.legend(handles=h, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.55, -0.11))
    save(fig, "fig2_auroc")


def fig3():
    c = pd.read_csv(ROOT / "tables/T3_contrasts_all_scenarios.csv")
    c = c[(c.weighting == "weighted") & (c.metric == "auroc") & (c.contrast == "PROV_LR - MIND_LR")]
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 4.0), sharey=True)
    sc = list(SCEN)
    for ax, oc in zip(axes, OUTC):
        d = c[c.outcome == oc].set_index("scenario")
        for i, s in enumerate(sc):
            r = d.loc[s]; colr = BLUE if s == "S0_primary" else GREY
            ax.plot([r.lo * 1000, r.hi * 1000], [i, i], color=colr, lw=1.6)
            ax.plot(r["diff"] * 1000, i, "o", color=colr, ms=4.5, mec="white", mew=0.8)
        ax.axvline(0, color="#444", lw=0.9)
        ax.set_title(OUTC[oc], fontsize=9, loc="left")
        ax.set_xlabel("Difference in AUROC (×0.001), paired 95% CI")
        ax.set_xlim(-10, 19)
        ax.grid(axis="y", visible=False)
    axes[0].set_yticks(range(len(sc)), [SCEN[s] for s in sc])
    axes[0].invert_yaxis()
    save(fig, "fig3_contrasts")


def fig4():
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 3.2))
    for ax, oc in zip(axes, OUTC):
        d = pd.read_csv(ROOT / f"results/metrics/calibration__{oc}__S0_primary.csv")
        d = d[d.weighting == "weighted"] if "weighted" in set(d.weighting) else d
        mx = 0
        for m, colr in [("MIND_LR", GREY), ("PATTERN_LR", GREEN), ("PROV_LR", ORANGE)]:
            g = d[d.method == m].sort_values("mean_pred")
            ax.plot(g.mean_pred, g.obs_rate, "-o", color=colr, ms=3, lw=1.3, label=m)
            mx = max(mx, g.mean_pred.max(), g.obs_rate.max())
        ax.plot([0, mx * 1.05], [0, mx * 1.05], "--", color="#555", lw=0.8)
        ax.set_title(OUTC[oc], fontsize=9, loc="left")
        ax.set_xlabel("Mean predicted risk (decile)")
        ax.set_ylabel("Observed proportion")
        ax.legend(frameon=False, fontsize=7.5)
    fig.tight_layout()
    save(fig, "fig4_calibration")


if __name__ == "__main__":
    fig1(); fig2(); fig3(); fig4()
    print("figures written to", OUT)
