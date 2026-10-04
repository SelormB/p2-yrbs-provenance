"""Pre-specified analysis scenarios (primary + sensitivity). Protocol section 10.

Each scenario is a dict of overrides consumed by pipeline.run_scenario. The list is fixed
before any real-data test-set scoring; additions after that point go in docs/DECISIONS.md
and are labelled post hoc in every table.
"""

SCENARIOS = {
    "S0_primary":   {"desc": "Primary: state+district surveys, audited window, within-survey PSU split"},
    "S_LSO":        {"desc": "Leave-sites-out split (transport to unseen jurisdictions)", "split": "leave_sites_out"},
    "S_TEMP":       {"desc": "Temporal split: latest cycle as test", "split": "temporal_last_year"},
    "S_NAT":        {"desc": "National survey only", "population": "national"},
    "S_NO2021":     {"desc": "Exclude 2021 (fall COVID-era administration)", "drop_years": [2021]},
    "S_PRE2023":    {"desc": "Exclude 2023 (mode-change cycle)", "drop_years": [2023]},
    "S_ONLY2023":   {"desc": "2023 only", "only_years": [2023]},
    "S_DROPABS":    {"desc": "Drop items not asked in >30% of surveys", "drop_absent_items_over": 0.30},
    "S_THR95":      {"desc": "Not-asked threshold 95% missing instead of 100%", "absent_threshold": 0.95},
    "S_PROX":       {"desc": "Add proximal suicide items (considered, plan)", "add_proximal": True},
    "S_FE":         {"desc": "Add site and year fixed effects to individual models", "add_site_year": True},
    "S_WTRAIN":     {"desc": "Normalized survey weights used in model training", "train_weights": True},
    "S_UNWT":       {"desc": "Include unweighted surveys (unweighted evaluation only)", "require_weight": False},
}

OUTCOME_SCENARIOS = {
    "any_attempt": list(SCENARIOS),
    "injurious_attempt": list(SCENARIOS),
}


def task_list():
    """Flat list of (outcome, scenario) pairs; index = Slurm array task id."""
    return [(o, s) for o, ss in OUTCOME_SCENARIOS.items() for s in ss]
