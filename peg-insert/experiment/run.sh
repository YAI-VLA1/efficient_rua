#!/bin/bash
set -eu
script_dir=$(cd "$(dirname "$0")" && pwd)
cd /root/cap-x
model=$1
condition=$2
trials=$3
workers=$4
shift 4
case "$condition" in
 C1) config=franka_robosuite_nut_assembly_privileged.yaml ;;
 C2) config=franka_nut_c2.yaml ;;
 C3) config=franka_nut_c3.yaml ;;
esac
root=${RUN_ROOT:-/root/capx-backup/corrected/runs}
export POSE_LOG="$root/poses/${model//\//_}/$condition"
export MUJOCO_GL=egl PYTHONUNBUFFERED=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH=/root/cap-x
exec .venv/bin/python "$script_dir/run.py" --model "$model" --config-path "env_configs/nut_assembly/$config" --output-dir "$root/$condition" --total-trials "$trials" --num-workers "$workers" --record-video False "$@"
