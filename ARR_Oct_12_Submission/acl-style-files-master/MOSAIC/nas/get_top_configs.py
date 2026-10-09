import csv
import os
import sys
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

rank_input = []
dict = {}
num = 0

# Budget options must match BUDGET_OPTIONS in run_longbench_lamp.py
surr = [64, 128, 256, 512, 1024, 2048, 4096]

# Get task name and method from command line arguments
if len(sys.argv) < 3:
    print("Usage: python get_top_configs.py <TASK_NAME> <METHOD>")
    print("Available tasks: SUMMARIZATION, SINGLE_DOCUMENT_QA, MULTI_DOCUMENT_QA, CODE, etc.")
    print("Available methods: snapkv, pyramidkv, h2o, cam, streamingllm, l2norm, adakv, headkv")
    sys.exit(1)

task_name = sys.argv[1]
method_name = sys.argv[2]
output_file = os.path.join(task_name, method_name, 'output.txt')


if not os.path.isfile(output_file):
    print(f"Error: {output_file} not found!")
    sys.exit(1)

print(f"Reading from: {output_file}")

def get_block_value(index, val):
#   print("index:{}\tval:{}".format(index, val))
  # parts = len(surr[index])
  parts = len(surr)
#   print("parts: ", parts, end = "\t")
  part_size = 1 / parts
#   print("part_size: ", part_size, end = "\t")
  part_index = min(int(val // part_size), parts - 1)
#   print("part_index: ", part_index, end = "\n")
  return part_index

def get_objective_values(block_values, csv_file):
  final_block_values = []
  for i in range(len(block_values)-2):
    # final_block_values.append(get_block_value(i, block_values[i]))
    final_block_values.append(surr[get_block_value(i, block_values[i])])
  mean_window_length = np.mean(final_block_values)
  print("final_block_values", final_block_values)
  print("Mean window length is: ",mean_window_length)
  # print("Penalty: ",block_values[-2])
  print("Evicted Attention score: ",block_values[-1])
  print("================================")
  
  # Export to CSV and sort by penalty
  file_exists = os.path.isfile(csv_file)
  
  # Read existing data if file exists
  rows = []
  if file_exists:
    with open(csv_file, 'r', newline='') as f:
      reader = csv.reader(f)
      headers = next(reader) if reader else ['mean_window_length', ' Attention Score']
      rows = list(reader)
  else:
    headers = ['mean_window_length','Attention Score']
  
  # Append new row
  new_row = [mean_window_length, block_values[-1]]
  rows.append(new_row)
  
  # Sort rows by penalty (column index 1)
  rows.sort(key=lambda x: float(x[1]))
  
  # Write sorted data back to CSV
  with open(csv_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(rows)
  
  return mean_window_length, block_values[-2], -1*block_values[-1]


with open(output_file, 'r') as f:
    reader = csv.reader(f, delimiter=' ')
    for row in reader:
      cur_rank = []
      cur_rank.append(float(row[-2]))
      cur_rank.append(float(row[-1]))
      num=num+1
      if cur_rank not in rank_input:
        rank_input.append(cur_rank)
        cur_rank_tuple = tuple(cur_rank)
        dict[cur_rank_tuple]=num
print(rank_input, end = "\n\n\n\n\n")
from ndsort import rank_one

rank_inp = np.array(rank_input)
rank_out = rank_one(rank_inp) 

for ranks in rank_out:
  print(ranks)
  print("hi")

indices = []
for val in rank_out[0]:
  print("indx :",dict[tuple(val)])
  indices.append(dict[tuple(val)])
#   print("row number:",dict[tuple(ranks)])
print(rank_out, end='\n\n\n\n')


import csv
rowcount = 1
res_archs = []
with open(output_file, 'r') as f:
    reader = csv.reader(f, delimiter=' ')
    for row in reader:
      if rowcount in indices:
        row = [float(x) for x in row]
        res_archs.append(row)
      rowcount += 1 
for x in res_archs:
  print(x)
  print(",")
print(len(res_archs))

# Collect window lengths and penalties for all architectures to create heatmap
all_window_lengths = []
all_penalties = []
for arch in res_archs:
    final_block_values = []
    for i in range(len(arch)-2):
        final_block_values.append(surr[get_block_value(i, arch[i])])
    all_window_lengths.append(final_block_values)
    all_penalties.append(arch[-1])  # Penalty is at index -2

# Combine window lengths with penalties and sort by penalty
combined_data = list(zip(all_window_lengths, all_penalties))
# combined_data.sort(key=lambda x: x[1])  # Sort by penalty

# Extract sorted window lengths
sorted_window_lengths = [data[0] for data in combined_data]
sorted_penalties = [data[1] for data in combined_data]

# Convert to numpy array for heatmap
window_matrix = np.array(sorted_window_lengths)

# Create comprehensive heatmap for all architectures
plt.figure(figsize=(max(12, len(res_archs) * 0.8), max(8, window_matrix.shape[1] * 0.8)))

# Use a colormap that clearly distinguishes different window lengths
color_map = plt.cm.RdYlGn_r  # Red-Yellow-Green colormap (reversed)

sns.heatmap(window_matrix,
            annot=True,
            fmt='d',
            cmap=color_map,
            cbar_kws={'label': 'Window Length'},
            xticklabels=[f'Block {i+1}' for i in range(window_matrix.shape[1])],
            yticklabels=[f'Arch {i+1}\n(Evicted Attention Score: {sorted_penalties[i]:.4f})' for i in range(len(res_archs))],
            linewidths=0.5,
            linecolor='gray')

# plt.title(f'Window Lengths Heatmap for All {len(res_archs)} Architectures\n(Sorted by Penalty)',
#           fontsize=14, fontweight='bold')
plt.title(f'Window Lengths Heatmap for All {len(res_archs)} Architectures\n({task_name} - No Sorting)',
          fontsize=14, fontweight='bold')
plt.xlabel('Block Index', fontsize=12)
plt.ylabel('Architecture (with Penalty)', fontsize=12)
plt.tight_layout()

# Save outputs inside task-specific + method subdirectory
top_configs_dir = os.path.join(task_name, method_name, 'top_configs')
os.makedirs(top_configs_dir, exist_ok=True)


# Save the heatmap with task name in filename
heatmap_file = os.path.join(top_configs_dir, 'all_archs_window_lengths_heatmap.png')
plt.savefig(heatmap_file, dpi=300, bbox_inches='tight')
plt.close()
print(f"\nComprehensive heatmap saved to: {heatmap_file}")

# CSV file inside task subdirectory
csv_file = os.path.join(top_configs_dir, 'objective_values.csv')

# Now call get_objective_values for each arch
for arch in res_archs:
    get_objective_values(arch, csv_file)
