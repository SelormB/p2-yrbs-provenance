"""Unit tests. All data here is synthetic and constructed for the test."""
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import average_precision_score, roc_auc_score

from p2prov import io as IO
from p2prov import metrics as M
from p2prov import provenance as PV
from p2prov import splits as SP
from p2prov.audit import choose_window
from p2prov.harmonize import make_outcome, resolve_concepts
from p2prov.methods import BlockedMethodError, MerchantStructurePreserving, Spec


def test_sas_layout_both_syntaxes():
    at = "/* INPUT trap in comment; */ DATA x; INPUT @1 sitecode $3. @4 year 4. @8 weight 10.4 ;"
    f = IO.parse_sas_layout(at)
    assert [(x.name, x.start, x.end, x.is_char) for x in f] == [
        ("sitecode", 1, 3, True), ("year", 4, 7, False), ("weight", 8, 17, False)]
    rg = "INPUT sitecode $ 1-3 year 4-7 ;"
    f2 = IO.parse_sas_layout(rg)
    assert [(x.name, x.start, x.end) for x in f2] == [("sitecode", 1, 3), ("year", 4, 7)]


def test_labels_parse():
    lab = IO.parse_sas_labels('LABEL qn29 = "Actually attempted suicide" q30=\'Injury\';')
    assert lab == {"qn29": "Actually attempted suicide", "q30": "Injury"}


def test_fixed_width_blank_is_missing(tmp_path):
    p = tmp_path / "d.dat"
    p.write_text("AB 2019 1\nCD 2021  \n")
    f = IO.parse_sas_layout("INPUT @1 s $2. @4 year 4. @9 q 1. ;")
    d = IO.read_fixed_width(p, f)
    assert d["q"].isna().tolist() == [False, True]
    assert d["s"].tolist() == ["AB", "CD"]


def test_outcome_coding_matches_cdc_qn_definitions():
    q29 = pd.Series([1, 2, 3, 4, 5, np.nan])
    y = make_outcome(q29, [2, 3, 4, 5], [1, 2, 3, 4, 5])
    assert y.tolist()[:5] == [0, 1, 1, 1, 1] and np.isnan(y.iloc[5])
    q30 = pd.Series([1, 2, 3, np.nan])  # did not attempt / yes / no
    y2 = make_outcome(q30, [2], [1, 2, 3])
    assert y2.tolist()[:3] == [0, 1, 0]  # QN30 denominator includes 'did not attempt'


def _toy():
    # two sites x two years; item a omitted by site B in 2019; item b absent everywhere in 2019
    return pd.DataFrame({
        "site": ["A"] * 4 + ["B"] * 4, "year": [2019, 2019, 2021, 2021] * 2,
        "a": [1, np.nan, 1, 2, np.nan, np.nan, 1, 1],
        "b": [np.nan, np.nan, 1, np.nan, np.nan, np.nan, 2, 2]})


def test_provenance_codes():
    df = _toy()
    p = PV.label_provenance(df, ["a", "b"], "site", "year")
    assert p["a"].tolist() == ["OBS", "NA_UNRES", "OBS", "OBS", "NA_SITE", "NA_SITE", "OBS", "OBS"]
    assert p["b"].tolist() == ["NA_YEAR", "NA_YEAR", "OBS", "NA_UNRES", "NA_YEAR", "NA_YEAR", "OBS", "OBS"]


def test_provenance_threshold():
    df = pd.DataFrame({"site": ["A"] * 20 + ["B"] * 20, "year": [2019] * 40,
                       "a": [np.nan] * 19 + [1] + [1] * 20})
    strict = PV.label_provenance(df, ["a"], "site", "year", absent_threshold=1.0)
    loose = PV.label_provenance(df, ["a"], "site", "year", absent_threshold=0.95)
    assert (strict["a"][:19] == "NA_UNRES").all()
    assert (loose["a"][:19] == "NA_SITE").all()


def test_skip_flag():
    df = pd.DataFrame({"g": [2, 2, 1], "d": [2, 1, 2]})
    assert PV.skip_consistent_flag(df, "g", [2], "d", 2).tolist() == [True, False, False]


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_weighted_metrics_match_sklearn(seed):
    rng = np.random.default_rng(seed)
    y = rng.integers(0, 2, 500); p = np.round(rng.random(500), 2); w = rng.gamma(2, 1, 500)
    assert M.auroc(y, p) == pytest.approx(roc_auc_score(y, p))
    assert M.auroc(y, p, w) == pytest.approx(roc_auc_score(y, p, sample_weight=w))
    assert M.average_precision(y, p, w) == pytest.approx(average_precision_score(y, p, sample_weight=w))


def test_calibration_recovers_perfect_model():
    rng = np.random.default_rng(3)
    p = rng.uniform(0.01, 0.5, 200000); y = (rng.random(200000) < p).astype(int)
    a, b = M.calibration_intercept_slope(y, p)
    assert abs(a) < 0.03 and abs(b - 1) < 0.03
    a2, b2 = M.calibration_intercept_slope(y, np.clip(p * 1.5, 0, 0.99))  # over-prediction
    assert a2 < -0.2


def test_thresholds_use_validation_only_and_hit_targets():
    rng = np.random.default_rng(4)
    p = rng.random(10000); y = (rng.random(10000) < p).astype(int)
    t = M.choose_threshold(y, p, "top_fraction", 0.10)
    assert np.mean(p >= t) == pytest.approx(0.10, abs=0.005)
    t2 = M.choose_threshold(y, p, "target_sensitivity", 0.8)
    assert M.threshold_metrics(y, p, t2)["sensitivity"] == pytest.approx(0.8, abs=0.005)


def test_design_bootstrap_resamples_psus_within_strata():
    strata = np.repeat(["h1", "h2"], 6); psu = np.array(["a", "a", "b", "b", "c", "c", "d", "d", "e", "e", "f", "f"])
    b = M.DesignBootstrap(strata, psu, 0)
    for _ in range(50):
        m = b.draw()
        assert m[:6].sum() == 6 and m[6:].sum() == 6  # n_h PSUs drawn per stratum
        assert all(m[i] == m[i + 1] for i in range(0, 12, 2))  # whole PSUs move together


def test_weighted_prevalence_unweighted_case():
    y = np.array([1, 0, 0, 0] * 50); w = np.ones(200)
    e, se, lo, hi = M.weighted_prevalence(y, w, np.repeat(["h"], 200), np.arange(200) % 20)
    assert e == pytest.approx(0.25) and se > 0 and lo < e < hi


def test_split_no_psu_straddles_and_freeze(tmp_path):
    df = pd.DataFrame({"survey_id": ["s1"] * 60 + ["s2"] * 60,
                       "design_psu": [f"s1|{i % 12}" for i in range(60)] + [f"s2|{i % 10}" for i in range(60)],
                       "row_id": [f"r{i}" for i in range(120)]})
    s = SP.within_survey_split(df, 7)
    assert df.assign(s=s).groupby("design_psu")["s"].nunique().max() == 1
    path = tmp_path / "split.parquet"
    SP.freeze(s, df["row_id"], path, {})
    SP.freeze(s, df["row_id"], path, {})  # identical: ok
    with pytest.raises(RuntimeError):
        SP.freeze(s.sample(frac=1, random_state=1).set_axis(s.index), df["row_id"], path, {})


def test_phmissbench_incompatible_returns_none(tmp_path):
    p = tmp_path / "pm.parquet"
    pd.DataFrame({"row_id": ["a"], "split": ["test"]}).to_parquet(p)
    assert SP.load_phmissbench_split(p, pd.Series(["a", "b"])) is None


def test_window_longest_run():
    aud = pd.DataFrame({"year": [2015, 2017, 2019, 2021, 2023], "o_asked_share": [1, 0.1, 1, 1, 1],
                        "predictor_items_in_year": [10] * 5, "predictor_items_total": [10] * 5})
    assert choose_window(aud, ["o"])["years"] == [2019, 2021, 2023]


def test_concept_resolution_flags_ambiguity():
    labels = {"qn1": "Felt sad or hopeless", "qn2": "Ever felt sad or hopeless at school", "qn3": "Carried a weapon"}
    r = resolve_concepts(labels, {"sad": "sad or hopeless", "weapon": "carried a weapon"}).set_index("concept")
    assert r.loc["sad", "status"] == "REVIEW" and r.loc["weapon", "matches"] == "qn3"


def test_merchant_method_is_blocked():
    with pytest.raises(BlockedMethodError, match="REQUIRES MERCHANT METHOD MATERIALS"):
        MerchantStructurePreserving(Spec(), 0).fit({})
