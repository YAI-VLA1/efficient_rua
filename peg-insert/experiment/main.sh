#!/bin/bash
set -euo pipefail
cd /root/cap-x
experiment=/root/capx-backup/experiment
run=/root/capx-backup/runs
while [[ ! -d /root/capx-backup/validation/oracle/C3/aaa_done_flag ]]; do sleep 3; done
shopt -s nullglob
passed=(/root/capx-backup/validation/oracle/C3/trial_*taskcompleted_1)
(( ${#passed[@]} >= 18 )) || { echo "C3 validation needs investigation"; exit 1; }
for group in 'openai/gpt-oss-20b C2 50' 'openai/gpt-oss-20b C3 50' 'gpt-6-astra C1 20' 'gpt-6-astra C3 20' 'Qwen2.5-Coder-7B-Instruct-AWQ C1 50' 'Qwen2.5-Coder-7B-Instruct-AWQ C2 50' 'Qwen2.5-Coder-7B-Instruct-AWQ C3 50'; do
  read -r model condition trials <<< "$group"
  used=$(df --output=used -B1 /root | tail -1)
  (( used < 45000000000 )) || { echo "Disk guard"; exit 1; }
  folder="$run/${model//\//_}/$condition"
  if [[ -d "$folder/aaa_done_flag" ]]; then continue; fi
  flags=()
  if [[ "$model" != openai/* ]]; then flags+=(--server-url http://127.0.0.1:8112/chat/completions); fi
  if [[ "$model" == Qwen* ]]; then
    until curl -sf http://127.0.0.1:8113/health >/dev/null; do sleep 10; done
  fi
  echo "Running $group"
  runuser -u capxtrial -- "$experiment/run.sh" "$model" "$condition" "$trials" 4 "${flags[@]}" >"/tmp/capx-${model//\//_}-$condition.log" 2>&1
  completed=("$folder"/trial_*)
  (( ${#completed[@]} == trials )) || { echo "Incomplete $group"; exit 1; }
  .venv/bin/python "$experiment/aggregate.py"
  sleep 2
done
