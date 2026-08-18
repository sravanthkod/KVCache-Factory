export PYTHONPATH="/home/sr5/at.manjunath/workspace/KVCache-Factory:${PYTHONPATH:-}"

python3 eval_top_configs.py "MULTI_DOCUMENT_QA" --method "streamingllm" \
                        --num_gpus 1 \
                        --data-dir /home/sr5/at.manjunath/workspace/KVCache-Factory/data/LongBench \
                        --model-path /home/sr5/at.manjunath/workspace/KVCache-Factory/Mistral-7B-Instruct-v0.2/ \
                        --attn-implementation flash_attention_2 