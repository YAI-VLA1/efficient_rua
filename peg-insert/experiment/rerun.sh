#!/bin/bash
# Start router.py separately before running. RUN_ROOT must be a fresh directory.
set -euo pipefail
source_dir=$(cd "$(dirname "$0")" && pwd)
root=${RUN_ROOT:-/root/capx-backup/corrected/runs}
cd /root/cap-x
export PYTHONPATH=$PWD
for c in C1 C3; do
  flag=0; if [[ $c == C3 ]]; then flag=1; fi
  runuser -u capxtrial -- env RUN_ROOT="$root" C3_VALIDATION=$flag "$source_dir/run.sh" oracle "$c" 20 4 --use-oracle-code True
  n=$(find "$root/oracle/$c" -maxdepth 1 -name 'trial_*' | wc -l)
  k=$(find "$root/oracle/$c" -maxdepth 1 -name 'trial_*taskcompleted_1' | wc -l)
  (( n==20 && k>=18 )) || exit 2
done
.venv/bin/python "$source_dir/verify_frames.py" "$root/poses/oracle/C1"
for c in C1 C2 C3; do
  folder="$root/openai_gpt-oss-20b/$c"
  for attempt in 1 2 3; do
    missing=$(python - "$folder" <<'PY'
import sys
from pathlib import Path
done = {int(p.parent.name.split('_')[1]) for p in Path(sys.argv[1]).glob('trial_*/summary.txt')}
print(','.join(map(str, sorted(set(range(1,51))-done))))
PY
)
    [[ -n "$missing" ]] || break
    runuser -u capxtrial -- env RUN_ROOT="$root" MISSING_TRIALS="$missing" "$source_dir/run.sh" openai/gpt-oss-20b "$c" 50 4
  done
  [[ $(find "$folder" -maxdepth 1 -name 'trial_*'|wc -l) == 50 ]] || exit 3
done
