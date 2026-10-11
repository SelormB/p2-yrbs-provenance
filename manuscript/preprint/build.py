"""Build the preprint PDF (PH-MissBench preprint style) from preprint.md + result tables.

python manuscript/preprint/build.py  ->  manuscript/preprint/preprint.pdf
"""
import re
import subprocess
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
T = ROOT / "tables"


def html_table(df, cls=""):
    h = "".join(f"<th>{c}</th>" for c in df.columns)
    rows = "".join("<tr>" + "".join(f"<td>{v}</td>" for v in r) + "</tr>" for r in df.astype(str).values)
    return f'<table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{rows}</tbody></table>'


def pct(x, d=1):
    return f"{100 * x:.{d}f}"


def tab_flow():
    a = pd.read_csv(T / "T_flow__any_attempt__site_level.csv")
    b = pd.read_csv(T / "T_flow__injurious_attempt__site_level.csv")
    lab = ["Records in the combined file, 1991–2023 release", "Survey years 2015–2023",
           "State and district surveys (national excluded)", "Weighted (representative) surveys",
           "Survey asked the outcome item", "Valid outcome response (analytic cohort)"]
    df = pd.DataFrame({"Step": lab,
                       "Any attempt: students": [f"{v:,}" for v in a.n],
                       "Any attempt: surveys": a.surveys,
                       "Injurious: students": [f"{v:,}" for v in b.n],
                       "Injurious: surveys": b.surveys})
    return html_table(df, "num")


def tab_perf():
    t = pd.read_csv(T / "T2_performance_primary.csv")
    t = t[t.weighting == "weighted"]
    order = ["PROV_HGB", "HGB_NATIVE", "PROV_LR", "MIND_LR", "PATTERN_LR", "MICE_LR", "MEAN_LR", "CC_LR",
             "DEMO_LR", "STRUCT_ONLY"]
    rows = []
    for m in order:
        a = t[(t.outcome == "any_attempt") & (t.method == m)].iloc[0]
        b = t[(t.outcome == "injurious_attempt") & (t.method == m)].iloc[0]
        rows.append([m.replace("_", "_<wbr>") + ("†" if m == "CC_LR" else ""), a.auroc, a.pr_auc, a.sens80_ppv,
                     b.auroc, b.pr_auc, b.sens80_ppv])
    df = pd.DataFrame(rows, columns=["Model", "AUROC", "PR-AUC", "PPV @80% sens.", "AUROC ", "PR-AUC ",
                                     "PPV @80% sens. "])
    head = ('<thead><tr><th></th><th colspan="3" class="grp">Any past-year attempt</th>'
            '<th colspan="3" class="grp">Injurious attempt</th></tr>'
            "<tr>" + "".join(f"<th>{c.strip()}</th>" for c in df.columns) + "</tr></thead>")
    body = "".join("<tr>" + "".join(f"<td>{v}</td>" for v in r) + "</tr>" for r in df.values)
    return f'<table class="num small">{head}<tbody>{body}</tbody></table>'


def tab_calib():
    t = pd.read_csv(T / "T2_performance_primary.csv")
    t = t[t.weighting == "weighted"]
    order = ["PROV_HGB", "HGB_NATIVE", "PROV_LR", "MIND_LR", "PATTERN_LR", "MICE_LR", "MEAN_LR", "CC_LR"]
    rows = []
    for m in order:
        a = t[(t.outcome == "any_attempt") & (t.method == m)].iloc[0]
        b = t[(t.outcome == "injurious_attempt") & (t.method == m)].iloc[0]
        rows.append([m, a.brier, a.cal_intercept, a.cal_slope, b.brier, b.cal_intercept, b.cal_slope])
    cols = ["Model", "Brier", "Intercept", "Slope", "Brier", "Intercept", "Slope"]
    head = ('<thead><tr><th></th><th colspan="3" class="grp">Any past-year attempt</th>'
            '<th colspan="3" class="grp">Injurious attempt</th></tr><tr>'
            + "".join(f"<th>{c}</th>" for c in cols) + "</tr></thead>")
    body = "".join("<tr>" + "".join(f"<td>{v}</td>" for v in r) + "</tr>" for r in rows)
    return f'<table class="num small">{head}<tbody>{body}</tbody></table>'


ITEM = {"qn12": ("Carried a weapon on school property", "Q12"),
        "qn14": ("Did not go to school because they felt unsafe", "Q14"),
        "qn16": ("Were in a physical fight", "Q16"),
        "qn19": ("Were ever physically forced to have sexual intercourse", "Q19"),
        "qn22": ("Experienced physical dating violence", "Q22"),
        "qn24": ("Were bullied on school property", "Q24"),
        "qn25": ("Were electronically bullied", "Q25"),
        "qn26": ("Felt sad or hopeless", "Q26"),
        "qn33": ("Currently smoked cigarettes", "Q33"),
        "qn36": ("Currently used electronic vapor products", "Q36"),
        "qn42": ("Currently drank alcohol", "Q42"),
        "qn48": ("Currently used marijuana", "Q48"),
        "qn49": ("Ever misused prescription pain medicine", "Q49"),
        "qn85": ("Got 8 or more hours of sleep", "Q85"),
        "qn87": ("Described grades as mostly A's or B's", "Q87")}


def tab_items():
    p = pd.read_csv(T / "T_provenance_overall.csv").pivot_table(index="item", columns="code", values="share",
                                                               fill_value=0)
    rows = []
    for k, (lab, q) in ITEM.items():
        r = p.loc[k]
        rows.append([k.upper(), lab, pct(r.get("OBS", 0)), pct(r.get("NA_SITE", 0)), pct(r.get("NA_YEAR", 0)),
                     pct(r.get("NA_UNRES", 0)), pct(r.get("OBS_NONSUB", 0))])
    df = pd.DataFrame(rows, columns=["Variable", "Description (CDC indicator)", "Observed (%)",
                                     "Not asked by survey (%)", "Not on year's questionnaire (%)",
                                     "Missing where asked (%)", "Not applicable (%)"])
    return html_table(df, "num small wrap2")


def tab_prev():
    p = pd.read_csv(T / "T_prevalence.csv")
    rows = []
    for y in [2015, 2017, 2019, 2021, 2023]:
        r = [str(y)]
        for oc in ["any_attempt", "injurious_attempt"]:
            for pop in ["site_level", "national"]:
                x = p[(p.outcome == oc) & (p.population == pop) & (p.year == y)].iloc[0]
                r += [f"{x.n:,}", f"{pct(x.weighted_prev)} ({pct(x.lo)}–{pct(x.hi)})"]
        rows.append(r)
    head = ('<thead><tr><th></th><th colspan="4" class="grp">Any past-year attempt</th>'
            '<th colspan="4" class="grp">Injurious attempt</th></tr><tr><th>Year</th>'
            + "<th>Site n</th><th>Site % (95% CI)</th><th>National n</th><th>National % (95% CI)</th>" * 2
            + "</tr></thead>")
    body = "".join("<tr>" + "".join(f"<td>{v}</td>" for v in r) + "</tr>" for r in rows)
    return f'<table class="num small">{head}<tbody>{body}</tbody></table>'


SCEN = {"S0_primary": "Primary", "S_LSO": "Jurisdictions held out", "S_TEMP": "Latest cycle held out",
        "S_NAT": "National survey only", "S_NO2021": "Excluding 2021", "S_PRE2023": "Excluding 2023",
        "S_ONLY2023": "2023 only", "S_DROPABS": "Often-omitted items dropped", "S_THR95": "95% not-asked rule",
        "S_PROX": "Ideation and plan added", "S_FE": "Site and year effects added",
        "S_WTRAIN": "Weighted training", "S_UNWT": "Unweighted surveys included"}
CON = ["PROV_LR - MIND_LR", "PATTERN_LR - MEAN_LR", "PROV_HGB - HGB_NATIVE", "PROV_LR - MICE_LR"]


def fmt_d(r):
    s = lambda v: f"{1000 * v:+.1f}".replace("-", "−")
    return f"{s(r['diff'])} ({s(r.lo)}, {s(r.hi)})"


def tab_contrasts(oc):
    c = pd.read_csv(T / "T3_contrasts_all_scenarios.csv")
    c = c[(c.weighting == "weighted") & (c.metric == "auroc") & (c.outcome == oc)]
    rows = []
    for s, lab in SCEN.items():
        d = c[c.scenario == s].set_index("contrast")
        rows.append([lab] + [fmt_d(d.loc[k]) if k in d.index else "—" for k in CON])
    df = pd.DataFrame(rows, columns=["Scenario"] + [k.replace(" - ", " − ") for k in CON])
    return html_table(df, "num small")


SUB = {"sex": {1: "Female", 2: "Male"}, "grade": {1: "9th", 2: "10th", 3: "11th", 4: "12th"},
       "race7": {1: "American Indian or Alaska Native", 2: "Asian", 3: "Black or African American",
                 4: "Hispanic or Latino", 5: "Native Hawaiian or Other Pacific Islander", 6: "White",
                 7: "Multiple races (non-Hispanic)"},
       "sexid": {1: "Heterosexual", 2: "Gay or lesbian", 3: "Bisexual", 4: "Describe identity another way",
                 5: "Not sure (questioning)"}}
SUBN = {"sex": "Sex", "grade": "Grade", "race7": "Race and ethnicity", "sexid": "Sexual identity",
        "site_type": "Survey type", "year": "Survey year"}


def tab_sub():
    s = pd.read_csv(T / "T4_subgroups_all.csv")
    s = s[(s.method == "PROV_LR") & (s.scenario == "S0_primary")]
    rows = []
    for g in ["sex", "grade", "race7", "sexid", "site_type", "year"]:
        a = s[(s.subgroup == g) & (s.outcome == "any_attempt")]
        for _, r in a.iterrows():
            lv = r.level
            try:
                lv = SUB.get(g, {}).get(int(float(lv)), str(int(float(lv))))
            except ValueError:
                pass
            b = s[(s.subgroup == g) & (s.outcome == "injurious_attempt") & (s.level == r.level)]
            bb = (f"{int(b.iloc[0].events):,}", f"{b.iloc[0].auroc:.3f} ({b.iloc[0].auroc_lo:.3f}–{b.iloc[0].auroc_hi:.3f})") \
                if len(b) else ("—", "—")
            rows.append([SUBN[g], lv, f"{int(r.n):,}", f"{int(r.events):,}",
                         f"{r.auroc:.3f} ({r.auroc_lo:.3f}–{r.auroc_hi:.3f})", *bb])
    head = ('<thead><tr><th></th><th></th><th colspan="3" class="grp">Any past-year attempt</th>'
            '<th colspan="2" class="grp">Injurious attempt</th></tr><tr><th>Characteristic</th><th>Level</th>'
            "<th>Test n</th><th>Events</th><th>AUROC (95% CI)</th><th>Events</th><th>AUROC (95% CI)</th></tr></thead>")
    body, last = "", None
    for r in rows:
        g = r[0] if r[0] != last else ""
        last = r[0]
        body += "<tr>" + "".join(f"<td>{v}</td>" for v in [g] + r[1:]) + "</tr>"
    return f'<table class="num small">{head}<tbody>{body}</tbody></table>'


def tab_brfss():
    b = pd.read_csv(ROOT / "results/brfss/metrics_brfss.csv")
    rows = []
    for m in ["MEAN_LR", "MIND_LR", "PROV_LR", "PATTERN_LR", "HGB_NATIVE", "PROV_HGB", "DEMO_LR"]:
        r = [m]
        for st in ["within_state", "leave_states_out"]:
            for met in ["auroc", "brier"]:
                x = b[(b.structure == st) & (b.method == m) & (b.metric == met)].iloc[0]
                r.append(f"{x.estimate:.3f} ({x.lo:.3f}–{x.hi:.3f})")
        rows.append(r)
    head = ('<thead><tr><th></th><th colspan="2" class="grp">Within-state PSU split</th>'
            '<th colspan="2" class="grp">Leave states out</th></tr><tr><th>Model</th>'
            "<th>AUROC</th><th>Brier</th><th>AUROC</th><th>Brier</th></tr></thead>")
    body = "".join("<tr>" + "".join(f"<td>{v}</td>" for v in r) + "</tr>" for r in rows)
    return f'<table class="num small">{head}<tbody>{body}</tbody></table>'


def figure(n, src, cap, w="100%"):
    return (f'<div class="figure"><img src="fig/{src}" style="width:{w}"/>'
            f'<p class="caption"><b>Figure {n}.</b> {cap}</p></div>')


BLOCKS = {
    "TAB_FLOW": lambda: '<p class="tcap"><b>Table 1.</b> Cohort flow, state and district surveys, 2015–2023.</p>' + tab_flow(),
    "TAB_PERF": lambda: ('<p class="tcap"><b>Table 4.</b> Survey-weighted test-set discrimination, primary analysis '
                         "(95% CI, 1,000 PSU bootstrap replicates).</p>" + tab_perf() +
                         '<p class="tnote">PPV @80% sens.: positive predictive value at the threshold giving 80% '
                         "sensitivity on the validation set. † Complete-case analysis scores only students with all "
                         "items observed (8.6% and 11.4% of the test sets), so its metrics describe a different, "
                         "smaller population.</p>"),
    "TAB_CALIB": lambda: ('<p class="tcap"><b>Table 5.</b> Survey-weighted Brier score and calibration intercept and '
                          "slope, primary analysis (95% CI).</p>" + tab_calib()),
    "TAB_ITEMS": lambda: ('<p class="tcap"><b>Table A1.</b> Predictors and the provenance of their values, all '
                          "1,008,297 records 2015–2023 (share of records, %).</p>" + tab_items()),
    "TAB_PREV": lambda: ('<p class="tcap"><b>Table A2.</b> Survey-weighted outcome prevalence by year, '
                         "state and district surveys (site) and the national survey (Taylor-linearized 95% CI).</p>"
                         + tab_prev()),
    "TAB_CON_ANY": lambda: ('<p class="tcap"><b>Table A3.</b> Pre-specified AUROC contrasts by scenario, any past-year '
                            "attempt (×0.001; survey-weighted; paired 95% CI, 1,000 replicates).</p>"
                            + tab_contrasts("any_attempt")),
    "TAB_CON_INJ": lambda: ('<p class="tcap"><b>Table A4.</b> Pre-specified AUROC contrasts by scenario, injurious '
                            "attempt (×0.001; survey-weighted; paired 95% CI, 1,000 replicates).</p>"
                            + tab_contrasts("injurious_attempt")),
    "TAB_SUB": lambda: ('<p class="tcap"><b>Table A5.</b> PROV_LR discrimination by subgroup, primary test sets '
                        "(survey-weighted AUROC, 95% CI). Subgroups with fewer than 30 events are not shown.</p>"
                        + tab_sub()),
    "TAB_BRFSS": lambda: ('<p class="tcap"><b>Table A6.</b> BRFSS 2023 contrasting test bed: ever-diagnosed '
                          "depressive disorder predicted from ACE items (survey-weighted, 95% CI, 1,000 replicates)."
                          "</p>" + tab_brfss()),
    "FIG1": lambda: figure(1, "fig1_provenance.png",
                           "Share of student records with each predictor absent, by provenance, all 1,008,297 "
                           "records 2015–2023 (national, state and district surveys). Most absence comes from "
                           "surveys that did not ask the item, not from students who skipped it.", "92%"),
    "FIG2": lambda: figure(2, "fig2_auroc.png",
                           "Survey-weighted test-set AUROC with 95% PSU-bootstrap intervals, primary analysis. "
                           "The diagnostic STRUCT_ONLY model uses only site, year and which items the survey asked."),
    "FIG3": lambda: figure(3, "fig3_contrasts.png",
                           "PROV_LR minus MIND_LR difference in survey-weighted AUROC (×0.001) across the "
                           "pre-specified scenarios, paired 95% CI, 1,000 replicates. Right of zero favours "
                           "provenance-split indicators. The national survey, where sites do not omit items, shows "
                           "no gain."),
    "FIG4": lambda: figure(4, "fig4_calibration.png",
                           "Survey-weighted calibration by decile of predicted risk, primary test sets. The dashed "
                           "line marks perfect calibration.", "88%"),
}


def main():
    md = (HERE / "preprint.md").read_text()
    for k, f in BLOCKS.items():
        v = f()
        if k.startswith("TAB"):
            v = f'<div class="tblock{" pb" if k == "TAB_SUB" else ""}">{v}</div>'
        md = md.replace(f"<<{k}>>", "\n\n" + v + "\n\n")
    assert "<<" not in md, re.findall(r"<<\w+>>", md)
    body = subprocess.run(["pandoc", "-f", "markdown-auto_identifiers+raw_html", "-t", "html"],
                          input=md, capture_output=True, text=True, check=True).stdout
    html = (HERE / "template.html").read_text().replace("$body$", body)
    (HERE / "preprint.html").write_text(html)
    pdf = HERE / "preprint.pdf"
    subprocess.run(["wkhtmltopdf", "--quiet", "--enable-local-file-access", "-s", "Letter",
                    "-T", "25mm", "-B", "22mm", "-L", "40mm", "-R", "40mm",
                    str(HERE / "preprint.html"), str(pdf)], check=False)
    print(subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout.split("Pages:")[1].split()[0],
          "pages")


if __name__ == "__main__":
    main()
