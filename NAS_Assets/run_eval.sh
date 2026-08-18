export PYTHONPATH="/home/snap_nas/sravanth/LLM/Token_Eviction/Dynamic_Methods/KVCache-Factory:${PYTHONPATH:-}"

# export CUDA_VISIBLE_DEVICES=0

# python3 eval_top_configs.py "MULTI_DOCUMENT_QA" --method "streamingllm" --num_gpus 1

export CUDA_VISIBLE_DEVICES=1

python3 eval_top_configs.py "CODE" --method "streamingllm" --num_gpus 1

# export CUDA_VISIBLE_DEVICES=2

# python3 eval_top_configs.py "SINGLE_DOCUMENT_QA" --method "streamingllm" --num_gpus 1
