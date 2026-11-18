"""Aggregate completed trial directories and preserve unavailable measurements."""
import csv
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parents[1]
ledger = {}
for p in (root/'experiment').glob('*usage.jsonl'):
    for line in p.read_text().splitlines():
        item = json.loads(line)
        ledger[item['sha256']] = item['usage']
rows = []
for cond in sorted((root/'runs').glob('*/C[123]')):
    model = cond.parent.name
    if model=='oracle':
        continue
    trials = {}
    for p in cond.glob('trial_*'):
        m = re.fullmatch(r'trial_(\d+)_sandboxrc_(-?\d+)_reward_[-.\d]+_taskcompleted_([01])', p.name)
        if not m or not (p/'summary.txt').is_file():
            continue
        i, rc, ok = map(int, m.groups())
        if i in trials:
            raise ValueError(f'Duplicate trial {p}')
        raw = p/'raw_response.sh'
        usage = ledger.get(hashlib.sha256(raw.read_bytes()).hexdigest()) if raw.exists() else None
        trials[i] = (ok, rc, usage)
    if not trials:
        continue
    n = len(trials)
    k = sum(v[0] for v in trials.values())
    prop = k/n
    z = 1.95996398454
    center = (prop + z*z/(2*n))/(1+z*z/n)
    delta = z*math.sqrt(prop*(1-prop)/n+z*z/(4*n*n))/(1+z*z/n)
    usage = [v[2] for v in trials.values() if v[2] is not None]
    row = dict(model=model, condition=cond.name, successes=k, trials=n, rate=prop,
               ci_low=max(0,center-delta), ci_high=min(1,center+delta),
               execution_rate=mean(v[1]==0 for v in trials.values()), usage_matched=len(usage))
    for field in ('prompt_tokens','completion_tokens','cost'):
        row['mean_'+field] = mean(u[field] for u in usage) if len(usage)==n and all(u.get(field) is not None for u in usage) else ''
    row["total_cost_usd"] = sum(u["cost"] for u in usage) if row["mean_cost"] != "" else ""
    rows.append(row)
if rows:
    with (root/'results.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    models = sorted({r['model'] for r in rows if 'astra' not in r['model'] and r['model']!='oracle'})
    labels={'openai_gpt-oss-20b':'GPT-OSS-20B','Qwen2.5-Coder-7B-Instruct-AWQ':'Qwen2.5-Coder-7B (AWQ)'}
    fig, ax = plt.subplots(figsize=(7.8,4.6))
    for m, model in enumerate(models):
        data = [r for r in rows if r['model']==model]
        x = [int(r['condition'][1])-1 + (m-(len(models)-1)/2)*.28 for r in data]
        y = [100*r['rate'] for r in data]
        ax.bar(x,y,width=.26,label=labels.get(model,model),yerr=[[100*max(0,r['rate']-r['ci_low']) for r in data],
             [100*max(0,r['ci_high']-r['rate']) for r in data]],capsize=4)
        for xpos, r in zip(x,data):
            ax.text(xpos,100*r['ci_high']+2,f"{r['successes']}/{r['trials']}",ha='center',fontsize=8)
    for r in rows:
        if 'astra' in r['model'] and r['condition']=='C1':
            ax.axhline(r['rate']*100,ls='--',color='#353945',label=f"Astra C1 (Codex, {r['successes']}/{r['trials']})")
        if 'astra' in r['model'] and r['condition']=='C3':
            ax.errorbar(2.32,100*r['rate'],yerr=[[100*max(0,r['rate']-r['ci_low'])],[100*max(0,r['ci_high']-r['rate'])]],fmt='D',color='#353945',capsize=3,label=f"Astra C3 (Codex, {r['successes']}/{r['trials']})")
    ax.set(ylim=(0,105),xticks=[0,1,2],xticklabels=['C1','C2','C3'],ylabel='Success rate (%)',
           title='Peg insertion with simulator ground-truth poses')
    ax.legend(loc='upper left',bbox_to_anchor=(1.01,1),frameon=False)
    fig.text(.5,.01,'Bars show successes per 50 trials with Wilson 95% intervals.',ha='center',fontsize=8)
    fig.tight_layout(rect=(0,.04,1,1))
    fig.savefig(root/'success-rates.png',dpi=170)
