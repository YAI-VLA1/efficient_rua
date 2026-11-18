#!/bin/bash
set -eu
while [ ! -x /root/qwen-serving/bin/vllm ] || [ ! -e /root/qwen-weights/tokenizer.json ]; do sleep 5; done
export OMP_NUM_THREADS=2
exec /root/qwen-serving/bin/vllm serve /root/qwen-weights --served-model-name Qwen2.5-Coder-7B-Instruct-AWQ --host 127.0.0.1 --port 8113 --dtype half --max-model-len 24576 --max-num-seqs 4 --gpu-memory-utilization 0.8 --enforce-eager --generation-config vllm
