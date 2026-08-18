#!/bin/bash

# Check if required number of arguments are passed
if [ "$#" -ne 5 ]; then
    echo "Usage: $0 <gpu_id> <method> <attn_implementation> <source_path> <model_path>"
    echo "Example: $0 0 SnapKV flash_attention_2 ./ /models/Llama-3-8B"
    exit 1
fi

# Assign command-line parameters to structured variables
GPU_ID=$1
METHOD=$2
ATTN_IMPL=$3
SOURCE_PATH=$4
MODEL_PATH=$5

# Export GPU visibility for the sub-processes
export CUDA_VISIBLE_DEVICES=${GPU_ID}

# Define your exact hardware/NPU aligned target budget pool
# BUDGET_POOL=(64 128 256 512 1024 2048)
# Override with BUDGET_POOL_OVERRIDE="1536 2048" (space-separated) to sweep a
# different set without touching the default used by other invocations.
if [ -n "${BUDGET_POOL_OVERRIDE:-}" ]; then
    read -ra BUDGET_POOL <<< "${BUDGET_POOL_OVERRIDE}"
else
    BUDGET_POOL=(64 128 256 512 1024)
fi

echo "========================================================="
echo " Starting Sweep Matrix for Method: ${METHOD}"
echo " Targeting Budgets: ${BUDGET_POOL[*]}"
echo "========================================================="

# Loop through each individual budget capacity in the array
for BUDGET in "${BUDGET_POOL[@]}"
do
    echo ""
    echo "--------------------------------------------------------"
    echo " Running Evaluation Setup for Budget: ${BUDGET} tokens"
    echo "--------------------------------------------------------"
    
    # Isolate save directories by budget and method to prevent files overwriting each other
    # e.g., results_long_bench/SnapKV_budget_512/
    CURRENT_SAVE_DIR="${SOURCE_PATH}/results_ruler/${METHOD}_budget_${BUDGET}"
    
    # Execute the primary Python script execution
    python3 run_ruler.py \
        --method "${METHOD}" \
        --model_path "${MODEL_PATH}" \
        --max_capacity_prompts "${BUDGET}" \
        --attn_implementation "${ATTN_IMPL}" \
        --save_dir "${CURRENT_SAVE_DIR}" \
        --use_cache True

    # Check execution status to ensure the run succeeded before moving forward
    if [ $? -eq 0 ]; then
        echo "Successfully completed evaluation for budget: ${BUDGET}"
    else
        echo "CRITICAL: Execution failed for budget: ${BUDGET}. Exiting sweep loop."
        exit 1
    fi
done

echo "========================================================="
echo " All budget configurations successfully evaluated!"
echo " Results stored in: ${SOURCE_PATH}results_long_bench/"
echo "========================================================="


# nohup bash infer.sh "0,1,2" "snapkv" "flash_attention_2" "./SNAP_KV_All_Budgets" "/home/snap_nas/sravanth/LLM/Token_Eviction/models/Llama-2-7b-chat-hf" > sravanth_logs/Llama-2-7B-chat-SNAP_KV_All_Budgets_09_06_2026.log &

#  nohup bash infer.sh "0,1,2" "h2o" "flash_attention_2" "./H2O_KV_All_Budgets" "/home/snap_nas/sravanth/LLM/Token_Eviction/models/Llama-2-7b-chat-hf" > sravanth_logs/Llama-2-7B-chat-H2O_All_Budgets_09_06_2026.log &

# nohup bash infer_all_budgets.sh "0" "adakv" "flash_attention_2" "./ADA_KV_All_Budgets" "/home/snap_nas/sravanth/LLM/Token_Eviction/models/Llama-2-7b-chat-hf" > sravanth_logs/Llama-2-7B-chat-ADA_KV_All_Budgets_13_07_2026.log &

# nohup bash infer_all_budgets.sh "0,1,2" "h2o" "flash_attention_2" "./H2O_KV_All_Budgets" "/home/snap_nas/sravanth/LLM/Token_Eviction/models/Llama-2-7b-chat-hf" > sravanth_logs/Llama-2-7B-chat-H2O_All_Budgets_13_07_2026.log &

# nohup bash infer_all_budgets.sh "0,1,2" "pyramidkv" "flash_attention_2" "./Pyramid_KV_All_Budgets" "/home/snap_nas/sravanth/LLM/Token_Eviction/models/Llama-2-7b-chat-hf" > sravanth_logs/Llama-2-7B-chat-PyramidKV_All_Budgets_13_07_2026.log &

# nohup bash infer_all_budgets.sh "0,1,2" "h2o" "flash_attention_2" "./H2O_KV_All_Budgets" "/data/sravanth/models/Llama-2-7b-chat-hf" > sravanth_logs/Llama-2-7B-chat-H2O_All_Budgets_14_07_2026.log &

# nohup bash infer_all_budgets.sh "0" "adakv" "flash_attention_2" "./ADA_KV_All_Budgets" "/data/sravanth/models/Llama-2-7b-chat-hf" > sravanth_logs/Llama-2-7B-chat-ADA_KV_All_Budgets_14_07_2026.log &


# nohup bash infer_all_budgets.sh "0,1,2" "snapkv" "flash_attention_2" "./Meta-Llama-3-8B-Instruct/SNAP_KV_All_Budgets" "/data/sravanth/models/Meta-Llama-3-8B-Instruct" > sravanth_logs/Meta-Llama-3-8B-Instruct-SNAP_KV_All_Budgets_14_07_2026.log &

# nohup bash infer_all_budgets.sh "0,1,2" "adakv" "flash_attention_2" "./Meta-Llama-3-8B-Instruct/ADA_KV_All_Budgets" "/data/sravanth/models/Meta-Llama-3-8B-Instruct" > sravanth_logs/Meta-Llama-3-8B-Instruct-ADA_KV_All_Budgets_14_07_2026.log &

# nohup bash infer_all_budgets_ruler.sh "0,1,2" "snapkv" "flash_attention_2" "./Meta-Llama-3-8B-Instruct/SNAP_KV_All_Budgets" "/data/sravanth/models/Meta-Llama-3-8B-Instruct" > sravanth_logs/Meta-Llama-3-8B-Instruct-SNAP_KV_All_Budgets_RULER_26_07_2026.log &

# nohup bash infer_all_budgets_ruler.sh "0,1,2" "h2o" "flash_attention_2" "./Meta-Llama-3-8B-Instruct/H2O_KV_All_Budgets" "/data/sravanth/models/Meta-Llama-3-8B-Instruct" > sravanth_logs/Meta-Llama-3-8B-Instruct-h2o_All_Budgets_RULER_04_08_2026.log &