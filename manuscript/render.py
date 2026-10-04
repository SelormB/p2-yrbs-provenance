"""Fill {{key}} placeholders in manuscript.md from results/stats.json.

Refuses synthetic-mode statistics. Unfilled keys are left as [MISSING:key] so they are visible.
Usage: python manuscript/render.py [--out manuscript/manuscript_rendered.md]
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fmt(v):
    if isinstance(v, list) and len(v) == 3:
        return f"{v[0]:.3f} (95% CI {v[1]:.3f} to {v[2]:.3f})"
    if isinstance(v, float):
        return f"{v:.3f}"
    if isinstance(v, list):
        return f"{v[0]}–{v[-1]}" if all(isinstance(x, int) for x in v) and v else str(v)
    return f"{v:,}" if isinstance(v, int) else str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", default=str(ROOT / "results/stats.json"))
    ap.add_argument("--out", default=str(ROOT / "manuscript/manuscript_rendered.md"))
    a = ap.parse_args()
    s = json.loads(Path(a.stats).read_text())
    if s.get("mode") != "REAL":
        raise SystemExit("Refusing to render: stats.json is not from a REAL-data run.")
    s.setdefault("window", s.get("window"))
    txt = (ROOT / "manuscript/manuscript.md").read_text()
    out = re.sub(r"\{\{(.+?)\}\}", lambda m: fmt(s[m.group(1)]) if m.group(1) in s else f"[MISSING:{m.group(1)}]", txt)
    Path(a.out).write_text(out)
    print(a.out, "unfilled:", len(re.findall(r"\[MISSING:", out)))


if __name__ == "__main__":
    main()
