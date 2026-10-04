"""BRFSS arm tests on SYNTHETIC data."""
import numpy as np
import pandas as pd

from p2prov import brfss as B


def test_brfss_provenance_classes():
    cfg = B.load_cfg()
    items = cfg["ace_items"]
    df = pd.DataFrame({"_state": [1, 1, 1, 2, 3]})
    for it in items:
        df[it] = [2.0 if it != "acepunch" else 1.0, np.nan, 7.0, np.nan, np.nan]
    df.loc[1, items[:4]] = 1.0          # answered first 4, then broke off
    df.loc[0, "acedivrc"] = 8.0          # parents not married
    p = B.label_provenance(df, cfg, main_states={1}, version_states={3})
    assert p.loc[0, "acedivrc"] == "OBS_NA_STRUCT"
    assert (p.loc[1, items[4:]] == "NA_BREAKOFF").all() and (p.loc[1, items[:4]] == "OBS").all()
    assert (p.loc[2] == "DK_REF").all()
    assert (p.loc[3] == "NA_STATE").all() and (p.loc[4] == "NA_VERSION").all()


def test_brfss_run_synthetic(tmp_path):
    s = B.run(tmp_path, tmp_path, synthetic=True, dev=True, df=B.synthetic_brfss(n_per=300))
    assert s["mode"] == "SYNTHETIC" and s["events"] > 0
    m = pd.read_csv(tmp_path / "results/brfss/metrics_brfss.csv")
    assert set(m.structure) == {"within_state", "leave_states_out"}
