#!/usr/bin/env bash
# Download the CDC YRBS 2023 combined high-school (SADC) ASCII files + SAS programs + User's Guide.
# Run on your MacBook or an HPC login node (CDC is not reachable from the build sandbox).
# Usage: bash scripts/00_acquire.sh [dest_dir]     (default data/raw)
set -euo pipefail
DEST="${1:-data/raw}"
BASE="https://www.cdc.gov/yrbs/files/sadc_2023/HS"
mkdir -p "$DEST"
FILES=(sadc_2023_national.dat sadc_2023_district.dat sadc_2023_state_a_d.dat sadc_2023_state_e_h.dat
       sadc_2023_state_i_l.dat sadc_2023_state_m.dat sadc_2023_state_n_p.dat sadc_2023_state_q_t.dat
       sadc_2023_state_u_z.dat 2023-SADC-SAS-Input-Program.sas 2023-SADC-SAS-Formats-Program.sas)
for f in "${FILES[@]}"; do
  if [[ -s "$DEST/$f" ]]; then echo "have $f"; continue; fi
  echo "get  $f"; curl -fL --retry 3 -o "$DEST/$f" "$BASE/$f"
done
curl -fL --retry 3 -o "$DEST/2023-YRBS-SADC-Documentation.pdf" \
  "https://www.cdc.gov/yrbs/media/pdf/2023/2023-YRBS-SADC-Documentation.pdf" || echo "guide download failed (non-fatal)"
( cd "$DEST" && { command -v sha256sum >/dev/null && sha256sum * || shasum -a 256 *; } > SHA256SUMS.txt )
echo "date_utc=$(date -u +%FT%TZ)" > "$DEST/ACQUIRED.txt"
echo "done -> $DEST"
