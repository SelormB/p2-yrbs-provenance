"""End-to-end run on SYNTHETIC fixtures (small scale). Verifies wiring, leakage guards, and stamping."""
import json

import numpy as np
import pandas as pd
import pytest

from p2prov import pipeline as PL
from p2prov.methods import METHODS, Spec
from p2prov.synthetic import make_fixtures


@pytest.fixture(scope="module")
def ctx(tmp_path_factory):
    root = tmp_path_factory.mktemp("p2")
    raw = make_fixtures(root / "raw", seed=11, scale=0.35)
    c = PL.Ctx(PL.load_config(), raw, root / "out", synthetic=True, dev=True)
    for f in (PL.stage_resolve, PL.stage_ingest, PL.stage_audit_years, PL.stage_provenance,
              PL.stage_splits, PL.stage_descriptives):
        f(c)
    return c


def test_run_is_stamped_synthetic(ctx):
    assert json.loads(ctx.p("RUN_MODE.json").read_text())["mode"] == "SYNTHETIC"
    assert "SYNTHETIC" in ctx.tag


def test_provenance_covers_every_cell(ctx):
    prov = pd.read_parquet(ctx.p("processed/provenance.parquet"))
    codes = set(np.unique(prov.drop(columns="row_id").to_numpy()))
    assert codes <= {"OBS", "OBS_NONSUB", "NA_SITE", "NA_YEAR", "NA_UNRES"}
    assert "NA_SITE" in codes and "NA_YEAR" in codes and "NA_UNRES" in codes


def test_primary_task_runs_and_has_no_test_leakage(ctx):
    preds = PL.stage_fit(ctx, "any_attempt", "S0_primary",
                         methods=["MEAN_LR", "MIND_LR", "PROV_LR", "HGB_NATIVE", "PATTERN_LR", "STRUCT_ONLY"])
    assert set(preds.split) == {"valid", "test"}  # training rows never scored
    F, split, _, _ = PL.scenario_data(ctx, "any_attempt", "S0_primary")
    train_ids = set(F["row_id"][split == "train"])
    assert not train_ids & set(preds.row_id)
    met = PL.stage_evaluate(ctx, "any_attempt", "S0_primary")
    thr = pd.read_csv(ctx.p("results/metrics/thresholds__any_attempt__S0_primary.csv"))
    assert (thr.chosen_on == "validation").all()
    au = met[(met.metric == "auroc") & (met.method == "MEAN_LR")]
    assert ((au.lo <= au.estimate) & (au.estimate <= au.hi)).all()


def test_imputer_fit_on_training_only(ctx):
    F, split, _, _ = PL.scenario_data(ctx, "any_attempt", "S0_primary")
    tr = PL._subset(F, split == "train")
    m = METHODS["MEAN_LR"](Spec(), 0).fit(tr)
    assert np.allclose(m.means.to_numpy(), tr["X"].mean().to_numpy(), equal_nan=True)


def test_leave_sites_out_has_disjoint_sites(ctx):
    F, split, _, _ = PL.scenario_data(ctx, "any_attempt", "S_LSO")
    s = pd.DataFrame({"site": F["S"]["sitecode"], "split": split})
    assert s.groupby("site")["split"].nunique().max() == 1
