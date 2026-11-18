"""Check task labels, seed pairing, prompt equality and calculate exact paired tests."""
import csv
import json
from pathlib import Path
from scipy.stats import binomtest

root = Path(__file__).resolve().parents[1]
runs = root/'runs'
reference = {}
rows = []
for model in sorted(runs.iterdir()):
    if model.name in ('poses','oracle') or not (model/'C1/aaa_done_flag').exists():
        continue
    baseline = {}
    prompt1 = None
    for cond in sorted(model.glob('C[123]')):
        if not (cond/'aaa_done_flag').exists():
            continue
        statuses = {}
        for trial in sorted(cond.glob('trial_*')):
            seed = int(trial.name.split('_')[1])
            pose = (runs/'poses'/model.name/cond.name/f'{seed:02}.json').read_bytes()
            assert reference.setdefault(seed,pose)==pose
            history = json.loads((trial/'all_responses.json').read_text())
            assert len(history)==1
            prompt = history[0]['initial_prompt']
            if prompt1 is None:
                prompt1 = prompt
            assert prompt[0]==prompt1[0]
            common = prompt1[1]['content'][0]['text']
            full = prompt[1]['content'][0]['text']
            assert full.startswith(common)
            addition = full[len(common):].strip().split('(')[0]
            assert addition=={'C1':'','C2':'get_nut_handle_to_center_offset','C3':'get_insertion_target_pose'}[cond.name]
            statuses[seed] = int(trial.name[-1])
        if cond.name=='C1':
            baseline=statuses
            continue
        assert statuses.keys()==baseline.keys()
        gain=sum(statuses[k]>baseline[k] for k in baseline)
        loss=sum(statuses[k]<baseline[k] for k in baseline)
        rows.append(dict(model=model.name,condition=cond.name,gains_vs_c1=gain,losses_vs_c1=loss,
                         exact_p=binomtest(gain,gain+loss).pvalue if gain+loss else 1.0))
if rows:
    with (root/'paired-checks.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=rows[0])
        w.writeheader()
        w.writerows(rows)
