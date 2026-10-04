"""Missing-data handling comparators and prediction models.

Every transformation is fit on the training rows only and then applied unchanged to
validation and test rows (no leakage). Methods share one interface:

    m = METHODS[name](spec, seed); m.fit(train_frame); p = m.predict_proba(frame)

where a frame is a dict with keys X (DataFrame of behavioral items, NaN = missing),
D (DataFrame of demographic categoricals), P (DataFrame of provenance codes, same
shape as X), S (DataFrame with site/year), y (array), w (array of survey weights).

Citations for each comparator are in docs/literature_review.md, section 3.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.linear_model import LogisticRegression

from .provenance import NA_SITE, NA_UNRES, NA_YEAR, OBS_NONSUB


class BlockedMethodError(RuntimeError):
    pass


@dataclass
class Spec:
    lr_C: float = 1.0
    hgb_params: dict = field(default_factory=lambda: dict(
        learning_rate=0.05, max_iter=500, max_leaf_nodes=31, min_samples_leaf=50,
        l2_regularization=1.0, early_stopping=True, validation_fraction=0.15,
        n_iter_no_change=30))
    mice_m: int = 5
    mice_max_iter: int = 5
    mice_fit_max_rows: int = 200_000  # imputation model fit on a seeded training subsample
    pattern_min_events: int = 50
    use_weights_in_training: bool = False
    add_site_year: bool = False


def _demo_dummies(D: pd.DataFrame, cats: dict | None) -> tuple[pd.DataFrame, dict]:
    """One-hot demographics with an explicit missing level; categories fixed from training."""
    D = D.astype("object").where(D.notna(), "NA")
    if cats is None:
        cats = {c: sorted(D[c].astype(str).unique()) for c in D.columns}
    parts = []
    for c, levels in cats.items():
        v = D[c].astype(str)
        for lv in levels[1:]:  # drop first level as reference
            parts.append(pd.Series((v == lv).astype(float), name=f"{c}={lv}", index=D.index))
    return pd.concat(parts, axis=1) if parts else pd.DataFrame(index=D.index), cats


def _site_year(S: pd.DataFrame, cats: dict | None) -> tuple[pd.DataFrame, dict]:
    return _demo_dummies(S.astype(str), cats)


class _Base:
    name = "base"
    model_kind = "lr"

    def __init__(self, spec: Spec, seed: int):
        self.spec, self.seed = spec, seed
        self.demo_cats = None
        self.sy_cats = None

    # ----- design matrix pieces -------------------------------------------------
    def _demo(self, F, fit):
        Z, cats = _demo_dummies(F["D"], None if fit else self.demo_cats)
        if fit:
            self.demo_cats = cats
        if self.spec.add_site_year:
            SY, c2 = _site_year(F["S"], None if fit else self.sy_cats)
            if fit:
                self.sy_cats = c2
            Z = pd.concat([Z, SY], axis=1)
        return Z

    def _clf(self):
        if self.model_kind == "lr":
            return LogisticRegression(C=self.spec.lr_C, max_iter=2000, solver="lbfgs")
        return HistGradientBoostingClassifier(random_state=self.seed, **self.spec.hgb_params)

    def _sw(self, F):
        if not self.spec.use_weights_in_training:
            return None
        w = np.asarray(F["w"], float)
        return w / w.mean()

    def coverage(self, F) -> np.ndarray:
        return np.ones(len(F["y"]), bool)


class CompleteCaseLR(_Base):
    """Complete-case analysis: fit on, and predict for, rows with all behavioral items observed."""
    name = "CC_LR"

    def _rows(self, F):
        return F["X"].notna().all(axis=1).to_numpy()

    def coverage(self, F):
        return self._rows(F)

    def fit(self, F):
        r = self._rows(F)
        Z = pd.concat([F["X"], self._demo(F, True)], axis=1)[r]
        sw = self._sw(F)
        self.clf = self._clf().fit(Z, F["y"][r], sample_weight=None if sw is None else sw[r])
        return self

    def predict_proba(self, F):
        Z = pd.concat([F["X"], self._demo(F, False)], axis=1).fillna(0)
        p = self.clf.predict_proba(Z)[:, 1]
        p[~self._rows(F)] = np.nan
        return p


class MeanImputeLR(_Base):
    """Single mean (proportion) imputation fit on training rows."""
    name = "MEAN_LR"
    indicators = "none"

    def _features(self, F, fit):
        X = F["X"]
        if fit:
            self.means = X.mean()
        Xi = X.fillna(self.means)
        parts = [Xi, self._demo(F, fit)]
        parts += self._indicator_block(F, fit)
        return pd.concat(parts, axis=1)

    def _indicator_block(self, F, fit):
        return []

    def fit(self, F):
        Z = self._features(F, True)
        self.cols = Z.columns
        self.clf = self._clf().fit(Z, F["y"], sample_weight=self._sw(F))
        return self

    def predict_proba(self, F):
        Z = self._features(F, False).reindex(columns=self.cols, fill_value=0.0)
        return self.clf.predict_proba(Z)[:, 1]


class MissingIndicatorLR(MeanImputeLR):
    """Mean imputation + one 'missing' indicator per item, all missingness sources pooled."""
    name = "MIND_LR"

    def _indicator_block(self, F, fit):
        M = F["X"].isna().astype(float).add_suffix("__miss")
        if fit:
            self.keep_ind = M.columns[M.std() > 0]
        return [M.reindex(columns=self.keep_ind, fill_value=0.0)]


class ProvenanceLR(MeanImputeLR):
    """Mean imputation + provenance-specific indicators (not-asked vs unresolved vs non-substantive)."""
    name = "PROV_LR"

    def _indicator_block(self, F, fit):
        P = F["P"]
        blocks = []
        for code, suf in [(NA_SITE, "__notasked"), (NA_YEAR, "__notasked"), (NA_UNRES, "__unres"),
                          (OBS_NONSUB, "__nonsub")]:
            blocks.append((P == code).astype(float).add_suffix(suf))
        B = pd.concat(blocks, axis=1)
        B = B.T.groupby(level=0).sum().T  # merge NA_SITE and NA_YEAR into one not-asked flag
        if fit:
            self.keep_ind = B.columns[B.std() > 0]
        return [B.reindex(columns=self.keep_ind, fill_value=0.0)]


class MICELR(_Base):
    """Multiple imputation by chained equations (m draws, posterior sampling), predictions averaged.

    Imputation models are fit on training rows only; outcome is NOT used in the imputation
    model so that test-time imputation is possible without the outcome (Sperrin et al. 2020).
    """
    name = "MICE_LR"

    def fit(self, F):
        D = self._demo(F, True)
        self.imps, self.clfs = [], []
        A = pd.concat([F["X"], D], axis=1)
        self.cols = A.columns
        rng = np.random.default_rng(self.seed)
        sub = (rng.choice(len(A), self.spec.mice_fit_max_rows, replace=False)
               if len(A) > self.spec.mice_fit_max_rows else np.arange(len(A)))
        for k in range(self.spec.mice_m):
            imp = IterativeImputer(max_iter=self.spec.mice_max_iter, sample_posterior=True,
                                   random_state=self.seed + k, min_value=0, max_value=1,
                                   skip_complete=True, keep_empty_features=True,
                                   n_nearest_features=15)
            imp.fit(A.iloc[sub])
            Ai = imp.transform(A)
            self.imps.append(imp)
            self.clfs.append(self._clf().fit(Ai, F["y"], sample_weight=self._sw(F)))
        return self

    def predict_proba(self, F):
        A = pd.concat([F["X"], self._demo(F, False)], axis=1).reindex(columns=self.cols, fill_value=0.0)
        ps = [c.predict_proba(i.transform(A))[:, 1] for i, c in zip(self.imps, self.clfs)]
        return np.mean(ps, axis=0)


class HGBNative(_Base):
    """Gradient boosting with native missing-value routing (missing-incorporated-in-attributes)."""
    name = "HGB_NATIVE"
    model_kind = "hgb"

    def _features(self, F, fit):
        return pd.concat([F["X"], self._demo(F, fit)], axis=1)

    def fit(self, F):
        Z = self._features(F, True)
        self.cols = Z.columns
        self.clf = self._clf().fit(Z, F["y"], sample_weight=self._sw(F))
        return self

    def predict_proba(self, F):
        return self.clf.predict_proba(self._features(F, False).reindex(columns=self.cols))[:, 1]


class ProvenanceHGB(HGBNative):
    """Gradient boosting with native NaN plus provenance indicators."""
    name = "PROV_HGB"

    def _features(self, F, fit):
        P = F["P"]
        na = ((P == NA_SITE) | (P == NA_YEAR)).astype(float).add_suffix("__notasked")
        un = (P == NA_UNRES).astype(float).add_suffix("__unres")
        return pd.concat([F["X"], na, un, self._demo(F, fit)], axis=1)


class PatternSubmodelLR(_Base):
    """Structure-aware: one logistic model per survey availability pattern (Mercaldo & Blume 2020).

    The availability pattern of a record is the set of items its survey asked (provenance not in
    NA_SITE/NA_YEAR). Each submodel uses only those items, trained on training rows whose surveys
    asked at least those items ('sharing' variant); item nonresponse inside the pattern is
    mean-imputed. Patterns with too few training events fall back to the largest-coverage model.
    """
    name = "PATTERN_LR"

    @staticmethod
    def _asked(F):
        P = F["P"]
        return ~(P.isin([NA_SITE, NA_YEAR]))

    def fit(self, F):
        self.F_train = F
        self.asked_tr = self._asked(F).to_numpy()
        self.means = F["X"].mean()
        self.items = list(F["X"].columns)
        self.cache = {}
        self.Dtr = self._demo(F, True)
        self.fallback_key = tuple(np.all(self.asked_tr, axis=0) | False)  # items asked everywhere
        return self

    def _submodel(self, key):
        if key in self.cache:
            return self.cache[key]
        cols = [it for it, a in zip(self.items, key) if a]
        rows = np.all(self.asked_tr[:, np.array(key, bool)], axis=1) if cols else np.ones(len(self.asked_tr), bool)
        y = np.asarray(self.F_train["y"])[rows]
        if y.sum() < self.spec.pattern_min_events or len(np.unique(y)) < 2:
            self.cache[key] = None
            return None
        Z = pd.concat([self.F_train["X"][cols].fillna(self.means[cols]), self.Dtr], axis=1)[rows]
        sw = self._sw(self.F_train)
        clf = self._clf().fit(Z, y, sample_weight=None if sw is None else sw[rows])
        self.cache[key] = (cols, clf)
        return self.cache[key]

    def predict_proba(self, F):
        asked = self._asked(F).to_numpy()
        D = self._demo(F, False)
        p = np.full(len(F["y"]), np.nan)
        keys = [tuple(r) for r in asked]
        for key in set(keys):
            idx = np.array([k == key for k in keys])
            sm = self._submodel(key) or self._submodel(self.fallback_key)
            if sm is None:
                continue
            cols, clf = sm
            Z = pd.concat([F["X"].loc[idx, cols].fillna(self.means[cols]), D.loc[idx]], axis=1)
            p[idx] = clf.predict_proba(Z)[:, 1]
        return p


class StructureOnly(_Base):
    """Diagnostic: site, year and availability pattern only, no individual responses.

    If this model approaches the individual-level models, apparent gains are coming from
    survey structure rather than student information (protocol 8.3).
    """
    name = "STRUCT_ONLY"
    model_kind = "hgb"

    def _features(self, F, fit):
        SY, cats = _site_year(F["S"], None if fit else self.sy_cats)
        if fit:
            self.sy_cats = cats
        na = (F["P"].isin([NA_SITE, NA_YEAR])).astype(float).add_suffix("__notasked")
        return pd.concat([SY, na], axis=1)

    fit = HGBNative.fit
    predict_proba = HGBNative.predict_proba


class DemoOnlyLR(MeanImputeLR):
    """Diagnostic baseline: demographics only."""
    name = "DEMO_LR"

    def _features(self, F, fit):
        return self._demo(F, fit)


class MerchantStructurePreserving(_Base):
    """INTEGRATION POINT — Merchant branching/structure-preserving method.

    BLOCKED — REQUIRES MERCHANT METHOD MATERIALS.
    This class intentionally implements nothing. It must be written from the co-authored
    branching-survey manuscript, not reconstructed. Expected interface: fit(F)/predict_proba(F)
    using F['X'], F['P'] (provenance codes), F['D'], and the skip-gate map in
    config/skip_gates.yaml. Register it in METHODS only after implementation and review.
    """
    name = "MERCHANT_SP"

    def fit(self, F):
        raise BlockedMethodError("BLOCKED — REQUIRES MERCHANT METHOD MATERIALS")

    predict_proba = fit


METHODS = {c.name: c for c in [CompleteCaseLR, MeanImputeLR, MissingIndicatorLR, MICELR,
                               HGBNative, ProvenanceLR, ProvenanceHGB, PatternSubmodelLR,
                               StructureOnly, DemoOnlyLR]}
BLOCKED = {"MERCHANT_SP": MerchantStructurePreserving}

# Pre-specified roles (protocol 7). Conventional vs provenance/structure-aware contrasts:
CONVENTIONAL = ["CC_LR", "MEAN_LR", "MIND_LR", "MICE_LR", "HGB_NATIVE"]
PROVENANCE_AWARE = ["PROV_LR", "PROV_HGB", "PATTERN_LR"]
DIAGNOSTIC = ["STRUCT_ONLY", "DEMO_LR"]
PRIMARY_CONTRASTS = [("PROV_LR", "MIND_LR"), ("PATTERN_LR", "MEAN_LR"), ("PROV_HGB", "HGB_NATIVE"),
                     ("PROV_LR", "MICE_LR")]
