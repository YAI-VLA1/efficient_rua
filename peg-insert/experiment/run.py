"""Run from the pinned CaP-X checkout. Seed placement and record the reset pose."""
import json
import os
from pathlib import Path
import numpy as np
import tyro
import requests

# The local reasoning model can decode 20,480 tokens more slowly than the
# upstream client's 200 s timeout. Leave simulator and IK requests unchanged.
_post = requests.post
def model_post(url, *args, **kwargs):
    if url == 'http://127.0.0.1:8112/chat/completions':
        kwargs['timeout'] = 850
    return _post(url, *args, **kwargs)
requests.post = model_post
from capx.envs import launch
from capx.envs.launch import LaunchArgs, main
from capx.envs.simulators.robosuite_nut_assembly import FrankaRobosuiteNutAssembly
from capx.envs.tasks.franka.franka_nut_assembly import FrankaNutAssemblyCodeEnv

_load_config = launch._load_config
def headless_config(args):
    factory, config, servers = _load_config(args)
    factory['cfg']['enable_render'] = False
    if os.getenv('DIAGNOSTIC_START'):
        config['resume_idx'] = int(os.environ['DIAGNOSTIC_START'])
    return factory, config, servers
launch._load_config = headless_config

_original_reset = FrankaRobosuiteNutAssembly.reset
def seeded_reset(self, *, seed=None, options=None):
    if seed is not None:
        np.random.seed(seed)
        self.robosuite_env.rng.bit_generator.state = np.random.default_rng(seed).bit_generator.state
    obs, info = _original_reset(self, seed=seed, options=options)
    if seed is not None:
        out = Path(os.environ['POSE_LOG'])
        out.mkdir(exist_ok=True, parents=True)
        (out / f'{seed:02}.json').write_text(json.dumps({k:v.tolist() for k,v in obs['nut_poses'].items()}))
    return obs, info
FrankaRobosuiteNutAssembly.reset = seeded_reset
previous_reset = FrankaNutAssemblyCodeEnv.reset
def fresh_reset(self, *, seed=None, options=None):
    global current_trial
    current_trial = seed
    for api in self._apis.values():
        api.cfg = None
    return previous_reset(self, seed=seed, options=options)
FrankaNutAssemblyCodeEnv.reset = fresh_reset

if os.environ.get('REPLAY_SOURCE'):
    from capx.envs import trial as trial_module
    def replay(args, config, obs):
        source = Path(os.environ['REPLAY_SOURCE'])
        [raw] = source.glob(f'trial_{current_trial:02}_*/raw_response.sh')
        history = json.loads((raw.parent/'all_responses.json').read_text())
        assert history[0]['initial_prompt'] == obs['full_prompt']
        return raw.read_text(), history[0].get('reasoning'), None
    trial_module._query_initial_code = replay
if os.environ.get('C3_VALIDATION') == '1':
    oracle = FrankaNutAssemblyCodeEnv.oracle_code
    start = oracle.index('# 3. Execute motion')
    finish = oracle.index('# 6. Final insertion')
    grasp = oracle[start:oracle.index('T_handle =',start)]
    FrankaNutAssemblyCodeEnv.oracle_code = (oracle[:start] +
        'desired_handle_pos, desired_handle_quat = get_insertion_target_pose()\n' +
        grasp + oracle[finish:])
    if os.environ.get('HOME_FIRST') == '1':
        FrankaNutAssemblyCodeEnv.oracle_code = 'goto_home_joint_position()\n' + FrankaNutAssemblyCodeEnv.oracle_code
if os.environ.get('MISSING_TRIALS'):
    from capx.envs import runner
    original_parallel = runner.run_parallel_with_setup
    def missing_only(trial_ids, **kwargs):
        missing = {int(i) for i in os.environ['MISSING_TRIALS'].split(',')}
        return original_parallel([i for i in trial_ids if i in missing], **kwargs)
    runner.run_parallel_with_setup = missing_only

if __name__ == '__main__':
    main(tyro.cli(LaunchArgs))
