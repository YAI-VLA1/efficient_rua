"""Collect the reset seed, final simulator decision and raw program hash."""
import csv
import hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
rows=[]
for model in sorted((root/'runs').iterdir()):
    if model.name=='poses':
        continue
    for cond in sorted(model.glob('C[123]')):
        if not (cond/'aaa_done_flag').exists():
            continue
        for trial in sorted(cond.glob('trial_*')):
            _,seed,_,rc,_,reward,_,completed=trial.name.split('_')
            raw=trial/'raw_response.sh'
            rows.append(dict(model=model.name,condition=cond.name,seed=int(seed),execution_rc=int(rc),
                task_completed=int(completed),shaped_reward=float(reward),
                response_sha256=hashlib.sha256(raw.read_bytes()).hexdigest() if raw.exists() else '',
                path=trial.relative_to(root)))
with (root/'trials.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=rows[0])
    w.writeheader()
    w.writerows(rows)
