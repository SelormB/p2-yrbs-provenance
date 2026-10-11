#!/bin/bash
# Stage F (overnight): BRFSS questionnaire versions 2 and 3; Indiana ACE check; BRFSS with 1,000 replicates;
# full 1,000-replicate re-evaluation of all 24 sensitivity tasks. Keeps the Mac awake while running.
# Log: logs/stageF.log
cd "$(dirname "$0")/.." || exit 1
exec > >(tee -a logs/stageF.log) 2>&1
echo "=== Stage F start $(date) ==="
caffeinate -dimsu -w $$ &
source .venv/bin/activate
python -m pip install -q -e ".[test]"
echo "--- download BRFSS versions $(date +%T) ---"
bash scripts/00_acquire_brfss.sh data/raw/brfss || echo "BRFSS download had errors"
echo "--- Indiana ACE check $(date +%T) ---"
python - <<'PY'
import pandas as pd, glob
for f in sorted(glob.glob('data/raw/brfss/LLCP*.XPT')):
    n = ace = 0
    for ch in pd.read_sas(f, format='xport', chunksize=100000, encoding='latin1'):
        ch.columns = [c.upper() for c in ch.columns]
        if 'ACEDEPRS' not in ch: break
        m = ch['_STATE'] == 18
        n += int(m.sum()); ace += int(ch.loc[m, 'ACEDEPRS'].notna().sum())
    print(f"INDIANA {f}: records={n} ace_answers={ace}")
PY
echo "--- BRFSS 1,000 replicates $(date +%T) ---"
python -m p2prov.cli brfss --raw data/raw/brfss --out . || echo "BRFSS FAILED"
for i in $(seq 0 25); do
  read o s <<< "$(python -m p2prov.cli list-tasks | awk -v i=$i '$1==i{print $2, $3}')"
  [[ "$s" == "S0_primary" ]] && continue
  python -m p2prov.cli evaluate --outcome $o --scenario $s --raw data/raw --out . > logs/tasks/evalF_$i.log 2>&1 && echo "eval $i $o $s ok $(date +%T)" || echo "eval $i FAILED $(date +%T)"
done
python -m p2prov.cli report --raw data/raw --out .
echo "STAGEF_DONE $(date)"
