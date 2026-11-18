"""Compute within-model paired changes and descriptive between-model interactions."""
import csv
import hashlib
from pathlib import Path
import numpy as np

root = Path(__file__).resolve().parents[1]
runs = root/'runs'
groups = {}
for path in runs.glob('*/C[123]'):
    if path.parent.name == 'oracle' or not (path/'aaa_done_flag').is_dir():
        continue
    groups[path.parent.name,path.name] = {
        int(p.name.split('_')[1]):int(p.name[-1]) for p in path.glob('trial_*')}
def pose(model, cond, idx):
    return (runs/'poses'/model/cond/f'{idx:02}.json').read_bytes()
def change(model, lo, hi, ids):
    for i in ids:
        assert pose(model,lo,i) == pose(model,hi,i), (model,lo,hi,i)
    return np.array([groups[model,hi][i]-groups[model,lo][i] for i in ids])
rows=[]
def record(name,values):
    n=len(values)
    rng=np.random.default_rng(20261117)
    draws=rng.choice(values,size=(20000,n),replace=True).mean(axis=1)
    a,b=np.quantile(draws,[.025,.975])
    rows.append(dict(comparison=name,paired_seeds=n,change_pp=100*values.mean(),
                     bootstrap_low_pp=100*a,bootstrap_high_pp=100*b))
for model in sorted({m for m,c in groups}):
    for lo,hi in [('C1','C2'),('C2','C3'),('C1','C3')]:
        if (model,lo) in groups and (model,hi) in groups:
            ids=sorted(groups[model,lo].keys() & groups[model,hi].keys())
            record(f'{model} {hi}-{lo}', change(model,lo,hi,ids))
    ref='gpt-6-astra'
    if model!=ref and all((m,c) in groups for m in [model,ref] for c in ['C1','C3']):
        ids=sorted(set.intersection(*(set(groups[m,c]) for m in [model,ref] for c in ['C1','C3'])))
        for i in ids:
            assert pose(model,'C1',i)==pose(ref,'C1',i)
        record(f'{model} minus {ref}, C3-C1',change(model,'C1','C3',ids)-change(ref,'C1','C3',ids))
qwen='Qwen3-14B-AWQ'
gpt='openai_gpt-oss-20b'
if all((m,c) in groups for m in (qwen,gpt) for c in ('C1','C3')):
    ids=sorted(set.intersection(*(set(groups[m,c]) for m in (qwen,gpt) for c in ('C1','C3'))))
    for i in ids:
        assert pose(qwen,'C1',i)==pose(gpt,'C1',i)
    record('Qwen3-14B minus GPT-OSS-20B, C3-C1',
           change(qwen,'C1','C3',ids)-change(gpt,'C1','C3',ids))
if rows:
    with (root/'paired-effects.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=rows[0])
        w.writeheader()
        w.writerows(rows)
