# Problem definition: Define the High Fidelity Function (HFF) here

import numpy as np
import os
import time

# from mp_gpu import get_score

# from objectives import get_objective_values
# NAS_BENCHMARK selects the objective module: "longbench" (default) or "ruler"
if os.environ.get("NAS_BENCHMARK", "longbench").lower() == "ruler":
    from run_ruler_lamp import get_objective_values
else:
    from run_longbench_lamp import get_objective_values

NAS_TASK_CATEGORY = os.environ.get("NAS_TASK_CATEGORY", "SINGLE_DOCUMENT_QA")
NAS_METHOD = os.environ.get("NAS_METHOD", "snapkv")

# Output directory for this task category + eviction method
NAS_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), NAS_TASK_CATEGORY, NAS_METHOD)
os.makedirs(NAS_OUTPUT_DIR, exist_ok=True)


# Initializing the problem 
def call_init():
    # Define the problem specs here
    global M
    global D
    global final_rows
    D = 32                   # Dimensions of decision variable space (one per model layer, 32 layers)
    N = int(os.environ.get("NAS_INIT_POINTS", str(2*D)))  # Starting number of points (default 2*D, unchanged)
    M = 2                    # Number of objectives
    num_repeat = 1           # Number of times the entire simulation is repeated for statistics. *******Keep it 1 for NAS*******
    budget = int(os.environ.get("NAS_EVAL_BUDGET", "1000"))  # Total HFF evaluations = N + num_iter (default 1000, unchanged)
    num_iter = budget-N      # Number of iterations 
    N_switch = budget + 1    # Parameter for convergence and exploration trade-off.
    gamma = 0.333            # Gamma is the CDF. Dont change.
    rng = 42              # seed for statistics
    true_front_flag = 0      # Set it 1 if true front is available for comparison else 0

    # If the simulation stops in between: 
    middle_drop = 0          # Set it 1 if the run stopped in between and follow the instructions below. 
    # There will be output.txt file. Find the number of rows in it. And determine in what repetion we are if num_repeat>1.
    # Ignore the repeats that are completed. Remember: Each repeat will have budget number of rows in the text file. 
    # After ignoring the repeats and corresponding number of rows, now determine how many number of rows are remaining.
    # If R repeats have happend, then ignore, the first budget*R rows and determine the remaining number of rows. (see last three comments for further instructions on this)  
    # If number of rows >= N then simply set N = number of rows in output.txt in line no. 15.
    # If number of rows < N, Dont change N in line no. 15 but set final_rows = number of rows in output.txt else let it be 0 below:
    # NAS_RESUME_ROWS: env-var resume — replay the first K rows of output.txt
    # (objectives read from the log instead of recomputed) and continue live
    # from row K+1. Requires identical seeds/anchors so X_init regenerates
    # identically. Default 0 = no resume (original behavior).
    final_rows = int(os.environ.get("NAS_RESUME_ROWS", "0"))
    if final_rows > 0:
        middle_drop = 1
    if middle_drop == 0:
        final_rows = 0       # This is obvious
    # If the middle drop happens after some repetitions (in case of num_repeat>1), change the num_repeats and random seed (manually) accordingly to prevent the rerun:
    # Say R repeats have happened and it stopped in (R+1)th run. Then set num_repeat = original value of "num_repeat" - R in line no. 17
    # and rng = 19929 + R 
    
    return D, N, M, num_iter, num_repeat, gamma, N_switch, true_front_flag, rng

def call_HFF(X_data):
    global final_rows

    X_point = np.copy(X_data) # X_point will be a 2d array in 0 to 1 scale.

    n = np.size(X_point, 0)   # number of points in x
    D = np.size(X_point, 1)   # Dimensions
    M = 2                     # Objectives
    f = np.zeros([n,M])
    
    # This is for recovery from log if middle_drop happens during initial LHS.
    # The replay applies ONLY to the first (init-batch) call: consume final_rows
    # once, then reset it, otherwise the BO loop's single-point calls try to
    # replay init rows into a (1,M) array and crash.
    output_path = os.path.join(NAS_OUTPUT_DIR, 'output.txt')
    if final_rows > 0 and len(X_point) > final_rows:
        my_data = np.loadtxt(output_path)
        f[0:final_rows,:] = my_data[0:final_rows,D:D+M]
        start_point = final_rows
        final_rows = 0  # consumed — subsequent calls compute everything live
    else:
        start_point = 0

    # This is for recovery from log if middle_drop happens during initial LHS.


    # If required: Denormalize X_point here to the desired scale and evaluate the function f. 

    for i in range(start_point, len(X_point)): # Dont change this line

        # NAS arch Objective evaluation starts here
        t0 = time.time()
        f[i][0], f[i][1] = get_objective_values(X_point[i])
        elapsed = time.time() - t0
        print(f"  [HFF] Config {i+1}/{len(X_point)}: f1={f[i][0]:.1f}, f2={f[i][1]:.4f}, time={elapsed:.1f}s")
        # NAS arch Objective evaluation ends here

        # This code is for creating the log
        HFF_D_stat = np.zeros((1,D+M))
        HFF_D_stat[0,0:D] = np.copy(X_point[i,:])
        HFF_D_stat[0,D:D+M] = np.copy(f[i,0:M])
        
        a = os.path.exists(output_path)
        if a: # file exists
            my_file = open(output_path,'a') # open in append mode
            np.savetxt(my_file,HFF_D_stat)
            my_file.close()
        else: 
            my_file = open(output_path, 'w+') # create and open the file in write mode
            np.savetxt(my_file,HFF_D_stat)
            my_file.close()
        # We will have each and every function call written in this output.txt row-wise. Repetitions will be stacked. 
        # This code is for creating the log

    return f

