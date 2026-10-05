"""SYNTHETIC fixtures that mimic the SADC file layout. FOR SOFTWARE TESTING ONLY.

Nothing produced from these fixtures is a scientific finding. Every output written in
synthetic mode is stamped SYNTHETIC by the pipeline.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

BEHAVIOR = {  # var: (label, base logit, loading on latent risk)
    "qn40": ("Felt sad or hopeless almost every day for 2 or more weeks in a row", -0.8, 1.2),
    "qn41": ("Were bullied on school property", -1.6, 0.8),
    "qn42": ("Were electronically bullied", -1.8, 0.8),
    "qn43": ("Were in a physical fight", -1.5, 0.6),
    "qn44": ("Carried a weapon on at least 1 day", -2.0, 0.4),
    "qn45": ("Were ever physically forced to have sexual intercourse", -2.6, 0.9),
    "qn46": ("Experienced physical dating violence (physically hurt on purpose by someone they were dating)", -2.4, 0.8),
    "qn47": ("Did not go to school because they felt they would be unsafe at school or on their way", -2.4, 0.6),
    "qn48": ("Currently drank alcohol (had at least one drink of alcohol on at least 1 day)", -1.4, 0.6),
    "qn49": ("Currently used marijuana", -1.8, 0.6),
    "qn50": ("Currently used electronic vapor products", -1.6, 0.5),
    "qn51": ("Currently smoked cigarettes", -3.0, 0.5),
    "qn52": ("Ever took prescription pain medicine without a doctor's prescription", -2.3, 0.7),
    "qn53": ("Did not get 8 or more hours of sleep", 1.0, 0.3),
    "qn54": ("Described their grades in school as mostly As or Bs", 0.9, -0.4),
}
GATE = "q33"  # synthetic 'ever smoked a cigarette' gate (1 yes, 2 no) for qn51


def _layout():
    spec = [("sitecode", True, 4), ("sitename", True, 24), ("sitetype", True, 8), ("sitetypenum", False, 1),
            ("year", False, 4), ("survyear", False, 2), ("weight", False, 10), ("stratum", False, 3),
            ("psu", False, 6), ("age", False, 1), ("sex", False, 1), ("grade", False, 1), ("race7", False, 1),
            ("sexid", False, 1), ("q27", False, 1), ("q28", False, 1), ("q29", False, 1), ("q30", False, 1),
            ("qn27", False, 1), ("qn28", False, 1), ("qn29", False, 1), ("qn30", False, 1), (GATE, False, 1)]
    spec += [(v, False, 1) for v in BEHAVIOR]
    pos, fields = 1, []
    for n, ch, wd in spec:
        fields.append((n, ch, pos, wd)); pos += wd
    return fields


def _sas_program(fields) -> str:
    lines = ["/* SYNTHETIC SAS input program for tests */", "DATA sadc;", "INFILE 'x.dat' LRECL=200;", "INPUT"]
    for n, ch, pos, wd in fields:
        lines.append(f"  @{pos} {n} {'$' if ch else ''}{wd}.")
    lines.append(";")
    labels = {"q27": "Seriously considered attempting suicide", "q28": "Made a suicide plan",
              "q29": "Actually attempted suicide", "q30": "Suicide attempt resulted in injury",
              "qn27": "Seriously considered attempting suicide", "qn28": "Made a plan about how they would attempt suicide",
              "qn29": "Actually attempted suicide", "qn30": "Had a suicide attempt that resulted in an injury, poisoning, or overdose",
              GATE: "Ever tried cigarette smoking"}
    labels.update({k: v[0] for k, v in BEHAVIOR.items()})
    lines.append("LABEL")
    for k, v in labels.items():
        lines.append(f"  {k} = \"{v}\"")
    lines.append(";\nRUN;")
    return "\n".join(lines)


def make_fixtures(out_dir: Path, seed: int = 1, scale: float = 1.0, data_files: list[str] | None = None) -> Path:
    rng = np.random.default_rng(seed)
    out_dir.mkdir(parents=True, exist_ok=True)
    fields = _layout()
    (out_dir / "2023-SADC-SAS-Input-Program.sas").write_text(_sas_program(fields))
    years = [2015, 2017, 2019, 2021, 2023]
    sites = [("XX", "United States", "National", 3, "sadc_2023_national.dat")]
    sites += [(f"S{i:02d}", f"State {i}", "State", 2, f) for i, f in enumerate(
        ["sadc_2023_state_a_d.dat"] * 2 + ["sadc_2023_state_e_h.dat"] * 2 + ["sadc_2023_state_i_l.dat"] * 2 +
        ["sadc_2023_state_m.dat"] + ["sadc_2023_state_n_p.dat"] * 2 + ["sadc_2023_state_q_t.dat"] +
        ["sadc_2023_state_u_z.dat"] * 2)]
    sites += [(f"D{i:02d}", f"District {i}", "District", 1, "sadc_2023_district.dat") for i in range(4)]
    site_eff = {s[0]: rng.normal(0, 0.35) for s in sites}
    rows = []
    for (sc, sn, st, stn, fn) in sites:
        for y in years:
            n = int(rng.integers(300, 600) * scale)
            strata = rng.integers(1, 4, n)
            psu = strata * 100 + rng.integers(1, 9, n)
            lat = rng.normal(0, 1, n) + site_eff[sc] + 0.1 * (y - 2019) / 2
            rec = {"sitecode": [sc] * n, "sitename": [sn] * n, "sitetype": [st] * n, "sitetypenum": [stn] * n,
                   "year": [y] * n, "survyear": [(y - 1991) // 2 + 1] * n,
                   "weight": rng.gamma(4, 0.25, n) * (100 if st != "National" else 1),
                   "stratum": strata, "psu": psu,
                   "age": rng.integers(2, 8, n), "sex": rng.integers(1, 3, n), "grade": rng.integers(1, 5, n),
                   "race7": rng.integers(1, 8, n), "sexid": rng.choice([1, 1, 1, 1, 2, 3, 4, 5, 6], n)}
            df = pd.DataFrame(rec)
            for v, (_, b0, b1) in BEHAVIOR.items():
                df[v] = (rng.random(n) < 1 / (1 + np.exp(-(b0 + b1 * lat)))).astype(float) + 1  # 1 yes 2 no -> fix below
                df[v] = np.where(df[v] == 2, 1.0, 2.0)  # CDC qn coding: 1 = yes, 2 = no
            ever = np.where(df["qn51"] == 1, 1, np.where(rng.random(n) < 0.3, 1, 2))
            df[GATE] = ever
            xb = -3.1 + 1.0 * lat + 0.25 * (df["sex"] == 1) + 0.4 * (df["sexid"].between(2, 4))
            att = rng.random(n) < 1 / (1 + np.exp(-xb))
            df["q29"] = np.where(att, rng.choice([2, 3, 4, 5], n, p=[.55, .3, .08, .07]), 1)
            df["q30"] = np.where(~att, 1, np.where(rng.random(n) < 0.32, 2, 3))
            df["q27"] = np.where(att | (rng.random(n) < 0.15 + 0.1 * (lat > 1)), 1, 2)
            df["q28"] = np.where(att | (rng.random(n) < 0.10), 1, 2)
            for q in ["27", "28"]:
                df[f"qn{q}"] = df[f"q{q}"]
            df["qn29"] = np.where(df["q29"] > 1, 1, 2)
            df["qn30"] = np.where(df["q30"] == 2, 1, 2)
            # --- missingness mechanisms -------------------------------------------------
            electronic = (st == "National" and y == 2023) or (st != "National" and y == 2023 and rng.random() < 0.5)
            if electronic:  # skip pattern: never smoked -> current smoking coded 'no' (skip-implied)
                df.loc[df[GATE] == 2, "qn51"] = 2.0
            for v in BEHAVIOR:  # item nonresponse, more among higher latent risk
                pm = 0.03 + 0.03 * (lat > 1)
                df.loc[rng.random(n) < pm, v] = np.nan
            for v in ["q29", "q30", "qn29", "qn30", "sexid", "race7"]:
                df.loc[rng.random(n) < 0.03, v] = np.nan
            if not electronic:  # paper: some q29/q30 inconsistencies edited to missing
                bad = (df["q29"] == 1) & (rng.random(n) < 0.01)
                df.loc[bad, ["q30", "qn30"]] = np.nan
            if st != "National":  # site-level omission of items
                for v in BEHAVIOR:
                    if rng.random() < 0.12:
                        df[v] = np.nan
                if rng.random() < 0.08:
                    df[["q30", "qn30"]] = np.nan
            if y == 2015:  # questionnaire-version absence
                df["qn52"] = np.nan
            if st != "National" and rng.random() < 0.04:  # unweighted survey
                df["weight"] = np.nan
            rows.append((fn, df))
    files = sorted({fn for fn, _ in rows})
    for f in files:
        frame = pd.concat([d for fn, d in rows if fn == f], ignore_index=True)
        with open(out_dir / f, "w") as fh:
            for rec in frame.itertuples(index=False):
                line = []
                for (n, ch, pos, wd) in fields:
                    v = getattr(rec, n)
                    if ch:
                        s = str(v)[:wd].ljust(wd)
                    elif v is None or (isinstance(v, float) and np.isnan(v)):
                        s = " " * wd
                    elif n == "weight":
                        s = f"{v:{wd}.4f}"[:wd]
                    else:
                        s = str(int(v)).rjust(wd)
                    line.append(s)
                fh.write("".join(line) + "\n")
    (out_dir / "SYNTHETIC_FIXTURE.txt").write_text("These files are synthetic test fixtures, not CDC data.\n")
    return out_dir
