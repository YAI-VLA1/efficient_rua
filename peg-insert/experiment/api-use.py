import ast
import csv
from pathlib import Path

root=Path(__file__).resolve().parents[1]
rows=[]
for path in sorted((root/'runs').glob('*/C[23]')):
    if path.parent.name=='oracle' or not (path/'aaa_done_flag').is_dir():
        continue
    func = {'C2':'get_nut_handle_to_center_offset','C3':'get_insertion_target_pose'}[path.name]
    used=valid=total=success=0
    for p in path.glob('trial_*'):
        total+=1
        try:
            tree=ast.parse((p/'code.py').read_text())
        except SyntaxError:
            continue
        valid+=1
        if any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id==func for n in ast.walk(tree)):
            used+=1
            success+=int(p.name[-1])
    rows.append(dict(model=path.parent.name,condition=path.name,total=total,parseable=valid,
                     direct_call_in_source=used,success_with_call_in_source=success))
if rows:
    with (root/'api-use.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=rows[0])
        w.writeheader()
        w.writerows(rows)
