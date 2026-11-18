import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from scipy.spatial.transform import Rotation
from capx.integrations.franka.nut_assembly_forms import FrankaNutOffsetApi, FrankaNutTargetApi
from capx.envs.tasks.franka.franka_nut_assembly import ORACLE_CODE

poses = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/root/capx-backup/runs/poses/openai_gpt-oss-20b/C1')
errors = []
for p in sorted(poses.glob('*.json')):
    data = {k: np.array(v) for k,v in json.loads(p.read_text()).items()}
    env = SimpleNamespace(get_observation=lambda: {'nut_poses':data})
    offset_api = object.__new__(FrankaNutOffsetApi)
    target_api = object.__new__(FrankaNutTargetApi)
    offset_api._env = target_api._env = env
    center,q = offset_api.get_object_pose('square nut')
    handle,_ = offset_api.get_object_pose('square nut handle')
    measured = Rotation.from_quat(np.roll(q,-1)).inv().apply(handle-center)
    returned = offset_api.get_nut_handle_to_center_offset('square nut')
    ns = {**target_api.functions(), **{k:lambda *a,**kw:None for k in ('goto_pose','close_gripper','goto_home_joint_position','open_gripper','print')}}
    exec(ORACLE_CODE,ns)
    pos,quat = target_api.get_insertion_target_pose()
    errors.append([np.linalg.norm(measured-returned),np.linalg.norm(pos-ns['desired_handle_pos']),
        (Rotation.from_quat(np.roll(quat,-1)).inv()*Rotation.from_quat(np.roll(ns['desired_handle_quat'],-1))).magnitude()])
assert len(errors)>=20 and np.max(errors)<1e-10
print('seeds',len(errors),'C2_offset',returned,'max errors [C2 m, C3 m, C3 rad]',np.max(errors,axis=0))
