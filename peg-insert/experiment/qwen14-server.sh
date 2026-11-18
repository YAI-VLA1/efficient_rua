#!/bin/bash
set -eu
export OMP_NUM_THREADS=2
exec /root/qwen-serving/bin/vllm serve /root/qwen14-weights --served-model-name Qwen3-14B-AWQ --host 127.0.0.1 --port 8113 --reasoning-parser qwen3 --dtype half --max-model-len 24576 --max-num-seqs 4 --gpu-memory-utilization 0.85 --enforce-eager --generation-config vllm
