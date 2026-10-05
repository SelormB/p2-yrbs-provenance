"""Train/validation/test structures. Splits are created once, hashed, and frozen.

Rows in YRBS are anonymous students; the PSU (school cluster) is the unit of assignment so
students from the same sampled cluster never straddle train and test.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def _assign_units(units: np.ndarray, fracs: tuple[float, float, float], rng) -> dict:
    u = rng.permutation(units)
    n = len(u)
    n_tr = int(round(fracs[0] * n))
    n_va = int(round(fracs[1] * n))
    lab = {}
    for i, k in enumerate(u):
        lab[k] = "train" if i < n_tr else ("valid" if i < n_tr + n_va else "test")
    return lab


def within_survey_split(df: pd.DataFrame, seed: int, fracs=(0.6, 0.2, 0.2)) -> pd.Series:
    """PSUs assigned to train/valid/test separately inside each survey (site x year)."""
    rng = np.random.default_rng(seed)
    out = pd.Series(index=df.index, dtype=object)
    for sid, g in df.groupby("survey_id", sort=True):
        psus = np.sort(g["design_psu"].unique())
        if len(psus) < 3:  # census or tiny surveys: fall back to record-level assignment
            lab = _assign_units(g.index.to_numpy(), fracs, rng)
            out.loc[g.index] = [lab[i] for i in g.index]
        else:
            lab = _assign_units(psus, fracs, rng)
            out.loc[g.index] = g["design_psu"].map(lab).to_numpy()
    return out


def leave_sites_out_split(df: pd.DataFrame, site: str, seed: int, fracs=(0.6, 0.2, 0.2)) -> pd.Series:
    """Whole sites (all years) held out: tests transport to jurisdictions never seen."""
    rng = np.random.default_rng(seed)
    lab = _assign_units(np.sort(df[site].astype(str).unique()), fracs, rng)
    return df[site].astype(str).map(lab)


def temporal_split(df: pd.DataFrame, year: str, seed: int, valid_frac: float = 0.2) -> pd.Series:
    """Latest cycle = test; earlier cycles split by PSU into train/valid."""
    last = df[year].max()
    out = pd.Series("test", index=df.index, dtype=object)
    early = df[df[year] < last]
    rng = np.random.default_rng(seed)
    psus = np.sort(early["design_psu"].unique())
    lab = _assign_units(psus, (1 - valid_frac, valid_frac, 0.0), rng)
    out.loc[early.index] = early["design_psu"].map(lab).replace({"test": "valid"}).to_numpy()
    return out


def split_hash(split: pd.Series, ids: pd.Series) -> str:
    payload = "\n".join(f"{i},{s}" for i, s in sorted(zip(ids.astype(str), split.astype(str))))
    return hashlib.sha256(payload.encode()).hexdigest()


def freeze(split: pd.Series, ids: pd.Series, path: Path, meta: dict) -> str:
    """Write split once. Refuses to overwrite a different frozen split."""
    h = split_hash(split, ids)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_suffix(".lock.json")
    if lock.exists():
        prev = json.loads(lock.read_text())
        if prev["sha256"] != h:
            raise RuntimeError(f"Frozen split {path} differs from recomputed split; refusing to overwrite. "
                               "Splits may not change after creation (protocol 6).")
        return h
    pd.DataFrame({"row_id": ids.to_numpy(), "split": split.to_numpy()}).to_parquet(path, index=False)
    lock.write_text(json.dumps({"sha256": h, **meta}, indent=2))
    return h


def load_phmissbench_split(path: Path, ids: pd.Series) -> pd.Series | None:
    """Return PH-MissBench frozen split aligned to ids, or None if absent / incompatible.

    Compatible = covers every cohort row_id with labels in {train, valid, test}. Anything less
    is reported as incompatible rather than patched, so the frozen test set is never altered.
    """
    if not path.exists():
        return None
    s = pd.read_parquet(path).set_index("row_id")["split"]
    aligned = ids.map(s)
    if aligned.isna().any() or not set(aligned.unique()) <= {"train", "valid", "test"}:
        return None
    return aligned
