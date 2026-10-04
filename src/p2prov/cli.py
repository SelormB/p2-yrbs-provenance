"""Command-line entry point: python -m p2prov.cli <stage> [options]."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import pipeline as PL
from .scenarios import task_list


def main(argv=None):
    ap = argparse.ArgumentParser(prog="p2prov")
    ap.add_argument("stage", choices=["resolve", "ingest", "audit", "provenance", "splits", "describe",
                                      "fit", "evaluate", "task", "all", "report", "list-tasks", "brfss"])
    ap.add_argument("--raw", default="data/raw", help="directory with CDC files")
    ap.add_argument("--out", default=".", help="output root (results/, tables/, figures/ ...)")
    ap.add_argument("--synthetic", action="store_true", help="fixture mode; outputs stamped SYNTHETIC")
    ap.add_argument("--dev", action="store_true", help="few bootstrap reps (MacBook)")
    ap.add_argument("--task-id", type=int, help="Slurm array index into task list")
    ap.add_argument("--outcome"); ap.add_argument("--scenario")
    ap.add_argument("--methods", nargs="*")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    out = Path(a.out)
    (out / "logs").mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(sys.stdout),
                                  logging.FileHandler(out / "logs" / f"{a.stage}.log")])
    if a.stage == "list-tasks":
        for i, t in enumerate(task_list()):
            print(i, *t)
        return
    if a.stage == "brfss":
        from . import brfss
        print(brfss.run(Path(a.raw), out, synthetic=a.synthetic, dev=a.dev))
        return
    ctx = PL.Ctx(PL.load_config(), a.raw, out, a.synthetic, a.dev)
    tasks = task_list()
    if a.task_id is not None:
        a.outcome, a.scenario = tasks[a.task_id]
    st = a.stage
    if st in ("resolve", "all"): PL.stage_resolve(ctx)
    if st in ("ingest", "all"): PL.stage_ingest(ctx)
    if st in ("audit", "all"): PL.stage_audit_years(ctx)
    if st in ("provenance", "all"): PL.stage_provenance(ctx)
    if st in ("splits", "all"): PL.stage_splits(ctx)
    if st in ("describe", "all"): PL.stage_descriptives(ctx)
    if st in ("fit", "task"): PL.stage_fit(ctx, a.outcome, a.scenario, a.methods, a.force)
    if st in ("evaluate", "task"): PL.stage_evaluate(ctx, a.outcome, a.scenario)
    if st == "all":
        for o, s in tasks:
            PL.stage_fit(ctx, o, s, a.methods, a.force)
            PL.stage_evaluate(ctx, o, s)
    if st in ("report", "all"):
        from . import report
        report.build(ctx)


if __name__ == "__main__":
    main()
