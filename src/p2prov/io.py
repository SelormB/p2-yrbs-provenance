"""Reading the CDC YRBS combined (SADC) ASCII files.

The fixed-width layout is never hard-coded: it is parsed from CDC's own SAS input
program so that a CDC re-release with shifted columns cannot silently misalign data.
Two INPUT syntaxes are supported:  ``@1 sitecode $5.``  and  ``sitecode $ 1-5``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Field:
    name: str
    start: int  # 1-based inclusive
    end: int    # 1-based inclusive
    is_char: bool


_AT_RE = re.compile(r"@\s*(\d+)\s+([A-Za-z_][A-Za-z0-9_]*)\s+(\$?)\s*(\d+)\.(\d*)")
_RANGE_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s+(\$?)\s*(\d+)\s*-\s*(\d+)")
_LABEL_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([\"'])(.*?)\2", re.S)


def _strip_comments(sas_text: str) -> str:
    sas_text = re.sub(r"/\*.*?\*/", " ", sas_text, flags=re.S)
    return re.sub(r"^\s*\*[^;]*;", " ", sas_text, flags=re.M)


def _input_block(sas_text: str) -> str:
    sas_text = _strip_comments(sas_text)
    m = re.search(r"\bINPUT\b(.*?);", sas_text, flags=re.I | re.S)
    if not m:
        raise ValueError("No INPUT statement found in SAS program")
    return m.group(1)


def parse_sas_layout(sas_text: str) -> list[Field]:
    block = _input_block(sas_text)
    fields: list[Field] = []
    for m in _AT_RE.finditer(block):
        start, name, dollar, width = int(m.group(1)), m.group(2), m.group(3), int(m.group(4))
        fields.append(Field(name.lower(), start, start + width - 1, dollar == "$"))
    if not fields:
        for m in _RANGE_RE.finditer(block):
            name, dollar, s, e = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
            fields.append(Field(name.lower(), s, e, dollar == "$"))
    if not fields:
        raise ValueError("Could not parse any fields from INPUT statement")
    names = [f.name for f in fields]
    if len(set(names)) != len(names):
        raise ValueError("Duplicate variable names in SAS layout")
    return fields


def parse_sas_labels(sas_text: str) -> dict[str, str]:
    """Return {variable: label} from LABEL statements (may be empty)."""
    labels: dict[str, str] = {}
    for blk in re.finditer(r"\bLABEL\b(.*?);", _strip_comments(sas_text), flags=re.I | re.S):
        for m in _LABEL_RE.finditer(blk.group(1)):
            labels[m.group(1).lower()] = " ".join(m.group(3).split())
    return labels


def _convert(df: pd.DataFrame, sel: list[Field]) -> pd.DataFrame:
    for f in sel:
        s = df[f.name].str.strip()
        if f.is_char and not re.fullmatch(r"q\d+[a-z]?", f.name):
            df[f.name] = s.replace("", np.nan)
        else:
            df[f.name] = pd.to_numeric(s.replace({"": np.nan, ".": np.nan}), errors="coerce")
    return df


def read_fixed_width(path: Path, fields: list[Field], usecols: list[str] | None = None,
                     years: list[int] | None = None, year_var: str = "year",
                     chunksize: int = 200_000) -> pd.DataFrame:
    """Read selected columns; optionally keep only rows whose year is in `years` (chunked, low memory)."""
    sel = [f for f in fields if usecols is None or f.name in usecols]
    missing = set(usecols or []) - {f.name for f in sel}
    if missing:
        raise KeyError(f"Variables not in SAS layout: {sorted(missing)}")
    colspecs = [(f.start - 1, f.end) for f in sel]
    names = [f.name for f in sel]
    reader = pd.read_fwf(path, colspecs=colspecs, names=names, dtype=str, header=None,
                         keep_default_na=False, chunksize=chunksize, encoding="latin1")
    parts = []
    for chunk in reader:
        if years is not None:
            y = pd.to_numeric(chunk[year_var].str.strip(), errors="coerce")
            chunk = chunk[y.isin(years)]
        if len(chunk):
            parts.append(_convert(chunk.copy(), sel))
    if not parts:
        return pd.DataFrame(columns=names)
    return pd.concat(parts, ignore_index=True)


def read_sadc(raw_dir: Path, data_files: list[str], sas_program: str,
              usecols: list[str] | None = None, years: list[int] | None = None) -> pd.DataFrame:
    sas_text = (raw_dir / sas_program).read_text(errors="replace")
    fields = parse_sas_layout(sas_text)
    frames = []
    for fn in data_files:
        p = raw_dir / fn
        if not p.exists():
            raise FileNotFoundError(f"{p} missing; run scripts/00_acquire.sh first")
        d = read_fixed_width(p, fields, usecols, years=years)
        d["source_file"] = fn
        d["row_id"] = [f"{fn}:{i}" for i in range(len(d))]
        frames.append(d)
    return pd.concat(frames, ignore_index=True)
