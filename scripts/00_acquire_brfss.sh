#!/usr/bin/env bash
# Download BRFSS 2023 main and version-1 XPT files (URLs verified 2026-10-04). Usage: bash scripts/00_acquire_brfss.sh [dest]
set -euo pipefail
DEST="${1:-data/raw/brfss}"; BASE="https://www.cdc.gov/brfss/annual_data/2023/files"
mkdir -p "$DEST"
for f in LLCP2023XPT.zip LLCP23V1_XPT.ZIP LLCP23V2_XPT.ZIP LLCP23V3_XPT.ZIP; do [[ -s "$DEST/$f" ]] || curl -fL --retry 3 -o "$DEST/$f" "$BASE/$f"; done
curl -fL --retry 3 -o "$DEST/codebook23.zip" "https://www.cdc.gov/brfss/annual_data/2023/zip/codebook23_llcp-v2-508.zip" || true
( cd "$DEST" && for z in *.zip *.ZIP; do unzip -oq "$z"; done; for f in *; do case "$f" in *.XPT|*.xpt) ;; *" "*) mv "$f" "$(echo $f | tr -d ' ')";; esac; done )
ls "$DEST"; echo "Expect LLCP2023.XPT and LLCP23V1.XPT (rename if CDC's names have spaces/other case)."
