"""Performance metrics with optional survey weights, and design-based bootstrap.

All metric functions accept w (case weights). Unweighted = ones. Survey-weighted metrics
estimate performance in the population the surveys represent; unweighted metrics describe
the analytic sample. Both are reported (protocol 9).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _w(w, n):
    return np.ones(n) if w is None else np.asarray(w, float)


def auroc(y, p, w=None):
    y, p = np.asarray(y), np.asarray(p, float)
    w = _w(w, len(y))
    order = np.argsort(p, kind="mergesort")
    y, p, w = y[order], p[order], w[order]
    wpos, wneg = w * (y == 1), w * (y == 0)
    # group ties
    uniq, start = np.unique(p, return_index=True)
    pos_g = np.add.reduceat(wpos, start)
    neg_g = np.add.reduceat(wneg, start)
    neg_below = np.cumsum(neg_g) - neg_g
    num = np.sum(pos_g * (neg_below + 0.5 * neg_g))
    den = wpos.sum() * wneg.sum()
    return float(num / den) if den > 0 else np.nan


def average_precision(y, p, w=None):
    """Weighted average precision (step-wise PR-AUC, no interpolation)."""
    y, p = np.asarray(y), np.asarray(p, float)
    w = _w(w, len(y))
    order = np.argsort(-p, kind="mergesort")
    y, p, w = y[order], p[order], w[order]
    tp = np.cumsum(w * (y == 1))
    fp = np.cumsum(w * (y == 0))
    last = np.r_[np.diff(p) != 0, True]  # thresholds at distinct scores
    tp, fp = tp[last], fp[last]
    P = tp[-1]
    if P <= 0:
        return np.nan
    prec = tp / np.maximum(tp + fp, 1e-12)
    rec = tp / P
    drec = np.diff(np.r_[0.0, rec])
    return float(np.sum(drec * prec))


def brier(y, p, w=None):
    w = _w(w, len(y))
    return float(np.sum(w * (np.asarray(p) - np.asarray(y)) ** 2) / w.sum())


def calibration_intercept_slope(y, p, w=None, iters=50):
    """Logistic recalibration. Slope: logit(y) ~ a + b*logit(p). Intercept (calibration-in-the-large):
    a with b fixed at 1 (offset model). Weighted Newton-Raphson."""
    y = np.asarray(y, float)
    w = _w(w, len(y))
    p = np.clip(np.asarray(p, float), 1e-8, 1 - 1e-8)
    lp = np.log(p / (1 - p))
    # slope model
    X = np.c_[np.ones_like(lp), lp]
    beta = np.array([0.0, 1.0])
    for _ in range(iters):
        mu = 1 / (1 + np.exp(-(X @ beta)))
        g = X.T @ (w * (y - mu))
        H = (X * (w * mu * (1 - mu))[:, None]).T @ X
        step = np.linalg.solve(H, g)
        beta += step
        if np.max(np.abs(step)) < 1e-10:
            break
    # intercept with offset
    a = 0.0
    for _ in range(iters):
        mu = 1 / (1 + np.exp(-(a + lp)))
        g = np.sum(w * (y - mu))
        h = np.sum(w * mu * (1 - mu))
        a += g / h
        if abs(g / h) < 1e-10:
            break
    return float(a), float(beta[1])


def threshold_metrics(y, p, thr, w=None):
    y = np.asarray(y)
    w = _w(w, len(y))
    pred = np.asarray(p) >= thr
    tp = np.sum(w * (pred & (y == 1))); fp = np.sum(w * (pred & (y == 0)))
    fn = np.sum(w * (~pred & (y == 1))); tn = np.sum(w * (~pred & (y == 0)))
    div = lambda a, b: float(a / b) if b > 0 else np.nan
    return {"sensitivity": div(tp, tp + fn), "specificity": div(tn, tn + fp),
            "ppv": div(tp, tp + fp), "npv": div(tn, tn + fn),
            "flagged_share": div(tp + fp, tp + fp + tn + fn)}


def choose_threshold(y, p, rule, value, w=None):
    """Threshold chosen on VALIDATION data only."""
    y, p = np.asarray(y), np.asarray(p, float)
    w = _w(w, len(y))
    if rule == "top_fraction":
        order = np.argsort(-p)
        cw = np.cumsum(w[order]) / w.sum()
        k = np.searchsorted(cw, value)
        return float(p[order][min(k, len(p) - 1)])
    if rule == "target_sensitivity":
        pos = y == 1
        order = np.argsort(-p[pos])
        cw = np.cumsum(w[pos][order]) / w[pos].sum()
        k = np.searchsorted(cw, value)
        return float(p[pos][order][min(k, pos.sum() - 1)])
    raise ValueError(rule)


def calibration_curve(y, p, w=None, bins=10):
    w = _w(w, len(y))
    q = np.unique(np.quantile(p, np.linspace(0, 1, bins + 1)))
    b = np.clip(np.searchsorted(q, p, side="right") - 1, 0, len(q) - 2)
    df = pd.DataFrame({"b": b, "y": y, "p": p, "w": w})
    g = df.groupby("b").apply(lambda d: pd.Series({
        "mean_pred": np.average(d.p, weights=d.w), "obs_rate": np.average(d.y, weights=d.w),
        "n": len(d)}), include_groups=False)
    return g.reset_index(drop=True)


def all_metrics(y, p, w=None, thresholds: dict | None = None) -> dict:
    out = {"auroc": auroc(y, p, w), "pr_auc": average_precision(y, p, w), "brier": brier(y, p, w)}
    out["cal_intercept"], out["cal_slope"] = calibration_intercept_slope(y, p, w)
    wv = _w(w, len(y))
    out["prevalence"] = float(np.sum(wv * np.asarray(y)) / wv.sum())
    out["mean_pred"] = float(np.sum(wv * np.asarray(p)) / wv.sum())
    for name, thr in (thresholds or {}).items():
        for k, v in threshold_metrics(y, p, thr, w).items():
            out[f"{name}_{k}"] = v
    return out


class DesignBootstrap:
    """PSU-with-replacement within strata (Rao-Wu style, n_h draws), vectorized.

    Strata with one PSU contribute their PSU unchanged. Returns per-row multiplicity vectors.
    """

    def __init__(self, strata, psu, seed):
        df = pd.DataFrame({"h": np.asarray(strata).astype(str), "c": np.asarray(psu).astype(str)})
        self.psu_codes, psu_uni = pd.factorize(df["c"])
        first = df.drop_duplicates("c")
        h_of_psu = pd.Series(first["h"].to_numpy(), index=first["c"].to_numpy()).reindex(psu_uni).to_numpy()
        order = np.argsort(h_of_psu, kind="mergesort")
        self.sorted_psu = order
        hs = h_of_psu[order]
        _, start, size = np.unique(hs, return_index=True, return_counts=True)
        self.slot_start = np.repeat(start, size)
        self.slot_size = np.repeat(size, size)
        self.n_psu = len(psu_uni)
        self.rng = np.random.default_rng(seed)

    def draw(self):
        u = self.rng.random(self.n_psu)
        pick = self.slot_start + np.floor(u * self.slot_size).astype(int)
        single = self.slot_size == 1
        pick[single] = self.slot_start[single]
        counts = np.bincount(self.sorted_psu[pick], minlength=self.n_psu)
        return counts[self.psu_codes].astype(float)


def bootstrap_ci(fn, y, p, base_w, boot: DesignBootstrap, reps: int, alpha=0.05):
    """Percentile CI for scalar or dict-valued fn(y, p, w)."""
    est = fn(y, p, base_w)
    draws = []
    for _ in range(reps):
        m = boot.draw()
        keep = m > 0
        draws.append(fn(y[keep], p[keep], (base_w[keep] if base_w is not None else 1.0) * m[keep]))
    if isinstance(est, dict):
        D = pd.DataFrame(draws)
        lo, hi = D.quantile(alpha / 2), D.quantile(1 - alpha / 2)
        return {k: (est[k], float(lo[k]), float(hi[k])) for k in est}
    a = np.asarray(draws, float)
    return est, float(np.nanquantile(a, alpha / 2)), float(np.nanquantile(a, 1 - alpha / 2))


def paired_difference_ci(fn, y, p1, p2, base_w, boot: DesignBootstrap, reps: int, alpha=0.05):
    """CI for fn(p1) - fn(p2) using the same bootstrap draws (paired)."""
    est = fn(y, p1, base_w) - fn(y, p2, base_w)
    d = []
    for _ in range(reps):
        m = boot.draw(); k = m > 0
        ww = (base_w[k] if base_w is not None else 1.0) * m[k]
        d.append(fn(y[k], p1[k], ww) - fn(y[k], p2[k], ww))
    d = np.asarray(d)
    return float(est), float(np.nanquantile(d, alpha / 2)), float(np.nanquantile(d, 1 - alpha / 2))


def weighted_prevalence(y, w, strata, psu):
    """Design-based prevalence with Taylor-linearized SE (with-replacement PSU approximation)."""
    y, w = np.asarray(y, float), np.asarray(w, float)
    W = w.sum(); est = np.sum(w * y) / W
    z = w * (y - est) / W
    df = pd.DataFrame({"h": np.asarray(strata), "c": np.asarray(psu), "z": z})
    zc = df.groupby(["h", "c"])["z"].sum().reset_index()
    var = 0.0
    for _, g in zc.groupby("h"):
        n = len(g)
        if n > 1:
            var += n / (n - 1) * np.sum((g["z"] - g["z"].mean()) ** 2)
    se = np.sqrt(var)
    return float(est), float(se), float(est - 1.96 * se), float(est + 1.96 * se)
