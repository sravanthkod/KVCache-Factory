# NAS run (same as before, method is auto-included in path)
NAS_METHOD=snapkv NAS_TASK_CATEGORY=SUMMARIZATION bash run_nas.sh

# Eval top configs (same as before, --method is used for path)
python3 eval_top_configs.py SUMMARIZATION --method snapkv --num_gpus 3

# Get top configs (now requires method arg)
python3 get_top_configs.py SUMMARIZATION snapkv


python3 eval_top_configs.py MULTI_DOCUMENT_QA --method snapkv --num_gpus 1

python3 eval_top_configs.py CODE --method snapkv --num_gpus 1