#!/bin/bash
set -eu
d=/root/capx-backup/corrected
model=Qwen3-14B-AWQ
until curl -sf http://127.0.0.1:8113/health >/dev/null; do sleep 5; done
for c in C1 C2 C3; do
  runuser -u capxtrial -- "$d/experiment/run.sh" "$model" "$c" 50 4 --server-url http://127.0.0.1:8112/chat/completions >"/tmp/corrected-$model-$c.log" 2>&1
  folder="$d/runs/$model/$c"
  [[ $(find "$folder" -maxdepth 1 -name 'trial_*'|wc -l) == 50 ]] || exit 1
  if [[ $c == C1 ]]; then
    ok=$(find "$folder" -maxdepth 1 -name 'trial_*_sandboxrc_0_*'|wc -l)
    if (( ok < 35 )); then echo "C1 execution gate: $ok/50"; exit 0; fi
  fi
done
