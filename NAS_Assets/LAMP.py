import ndsort
import HFF_mod
import numpy as np
from scipy.stats import qmc
import matplotlib.pyplot as plt
from sklearn.neural_network import MLPClassifier as MLP
from scipy.optimize import differential_evolution as de
import matplotlib

import warnings
warnings.filterwarnings("ignore")
matplotlib.use('Agg')
import os
import time

# Output directory for this task category + eviction method (same as HFF_mod.py)
NAS_TASK_CATEGORY = os.environ.get("NAS_TASK_CATEGORY", "SINGLE_DOCUMENT_QA")
NAS_METHOD = os.environ.get("NAS_METHOD", "snapkv")
NAS_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), NAS_TASK_CATEGORY, NAS_METHOD)
os.makedirs(NAS_OUTPUT_DIR, exist_ok=True)


FIG_DIR = os.path.join(NAS_OUTPUT_DIR,"run_files")

os.makedirs(FIG_DIR,exist_ok=True)


# Training Data Generation (TDG) for training the binary classifier for single objectives
def call_TDG1(HFF_D_set, M, gamma, obj):
    dataset = np.copy(HFF_D_set) # A 2d array of size N x D+M. 
    # Each row is D 0 to 1 scaled Inputs + M original scaled High fidelity function values.
    N = np.size(dataset,0) # Number of points
    D = np.size(dataset,1) - M # Number of input dimensions.
    
    # 1. I want to extract the outputs
    Y = np.copy(dataset[:,D+obj])
    tau = np.quantile(Y,gamma)
    
    # 2. We can decide how many fronts can be taken for class 0 - we can also use crowding distance to select few from given front
    # As of now, just taking rank 1 as class 0

    # 3. List of data for ANN classifier
    for i in range(N):
        if Y[i] <= tau:         
            y_label = 0 # Fixing the label - l(x)
            classification_tuple = np.append(dataset[i,0:D], y_label) # A list of D+1 entries: D inputs, and 1 label  
        else:           
            y_label = 1 # Fixing the label - g(x)
            classification_tuple = np.append(dataset[i,0:D], y_label) # A list of D+1 entries: D inputs, and 1 label  
        if i == 0:
            ANN_D_set = np.copy(classification_tuple)
        else:
            ANN_D_set = np.vstack((ANN_D_set, classification_tuple)) 
        # An array of size Nx(D+1): D are inputs and last is output label.

    return ANN_D_set

# Training Data Generation (TDG) for training the binary classifier for all objectives
def call_TDG(HFF_D_set, rnk1idx, M):
    dataset = np.copy(HFF_D_set) # A 2d array of size N x D+M. 
    # Each row is D 0 to 1 scaled Inputs + M original scaled High fidelity function values.
    N = np.size(dataset,0) # Number of points
    D = np.size(dataset,1) - M # Number of input dimensions.

    # 3. List of data for ANN classifier
    for i in range(N):
        if rnk1idx[i] == 1:         
            y_label = 0 # Fixing the label - l(x)
            classification_tuple = np.append(dataset[i,0:D], y_label) # A list of D+1 entries: D inputs, and 1 label  
        else:           
            y_label = 1 # Fixing the label - g(x)
            classification_tuple = np.append(dataset[i,0:D], y_label) # A list of D+1 entries: D inputs, and 1 label  
        if i == 0:
            ANN_D_set = np.copy(classification_tuple)
        else:
            ANN_D_set = np.vstack((ANN_D_set, classification_tuple)) 
        # An array of size Nx(D+1): D are inputs and last is output label.

    return ANN_D_set

# Training the ANN
def call_train_NN(ANN_D_set):
    D = np.size(ANN_D_set,1) - 1 # Number of input dimensions for the binary classifier
    X = ANN_D_set[:,0:D]
    Y = ANN_D_set[:,D]
    NN_clf = MLP(hidden_layer_sizes=(32,32)) # MLP    
    NN_clf.fit(X,Y) # train the model
    return NN_clf

# Objective function for convergence
def call_NN_ACF_obj(X_pred, NN_clf):
    Y_pred_proba = NN_clf.predict_proba([X_pred]) # Prediciton of Probabilities
    # We trained the NN with a 2D array - rows were data points and columns were dimensions.
    # The predict_proba also requires a 2D array - row should be a data point and columns should be dimensions.
    # X_pred is 1d array - its a vector with D dimensions.
    # [X_pred] is a 2d array - its a matrix with 1 row and D columns.
    # Y_pred_proba comes out as a 2d array - rows correspond to data points and 2 columns corresponding to probabilities of 2 classes.
    # This is not a requirement with class predicitons.
    # ie, class predictions will be a 1d list/array because its just a vector: for example, if our objective had been the class instead of probability then if we have Y_pred = NN_clf.predict([X_pred]), then NN_obj = Y_pred[0]
    NN_obj = Y_pred_proba[0][0] # I need the class 0 probability which is the 0th entry in 0th list of the 2d array Y_pred_proba
    NN_obj = -NN_obj # The real objective is to maximize.
    return NN_obj

# Plot and save the Pareto front
def plot_pareto(HFF_D_set, M, true_front_flag, n_iter, HFF_counter):
    dataset = np.copy(HFF_D_set) # A 2d array of size N x D+M. 
    # Each row is D 0 to 1 scaled Inputs + M original scaled High fidelity function values.
    N = np.size(dataset,0) # Number of points
    D = np.size(dataset,1) - M # Number of input dimensions.
    if M == 3:
        fig = plt.figure()
        ax = fig.gca(projection ='3d')   
    if true_front_flag == 1:
        true_front = HFF_mod.true_front()
        if M == 3:
            ax.plot(true_front[:,0], true_front[:,1], true_front[:,2], 'o', label = 'True Front')
        else:
            plt.plot(true_front[:,0],true_front[:,1],'o',label = 'True Front')

    my_pop = np.copy(dataset[:,D:D+M])
    obt_front,_ = ndsort.rank_one(my_pop)
    if M == 3:
        ax.plot(obt_front[:,0], obt_front[:,1], obt_front[:,2], '*', label = 'Obtained Front')
    else:
        plt.plot(obt_front[:,0], obt_front[:,1], '*', label = 'Obtained Front')
    
    plt.legend()
    str1 = 'Run ' + str(n_iter+1) 
    str2 = ' | HFF calls = ' + str(HFF_counter)
    f = str1 + '.png'
    fig_title = str1 + str2
    plt.title(fig_title)
    plt.xlabel('(Minimize) f1')
    plt.ylabel('(Minimize) f2')
    if M == 3:
        ax.set_zlabel('(Minimize) f3')
    # plt.savefig(f)
    # plt.savefig(os.path.join("/home/snap_nas/sravanth/LLM/Token_Eviction/LongBench_ICASSP_Work/LongBench/run_files",f))
    # plt.savefig(os.path.join(NAS_OUTPUT_DIR, f))
    plt.savefig(os.path.join(FIG_DIR,f))
    plt.close() 
    return ()


if __name__ == '__main__':
    # Step 0: Initialize
    D_input, N_start, M_obj, num_iter, num_repeat, gamma, N_switch, true_front_flag, rng_start = HFF_mod.call_init()
    rng = rng_start # seed for statistics
    total_search_start = time.time()

    for n_repeat in range(num_repeat): # multiple simulations for statistics
            
        # Step 1: Generate the initial points & objectives
        N = N_start # starting LHS points
        D = D_input # input dimensions.
        M = M_obj # output dimensions. 
        HFF_counter = N_start # counter for high fidelity calls
        
        # If we are repeating the BO for say 21 times, then we need 21 seeds for 21 repetitions. 
        # Use the same 21 seeds in the same sequence in other optimization algorithms for comparisons.
        # By fixing the same seed in different optimization algorithms we are ensuring that starting point is same for all. 
        rng = rng + 1 # random number generator (rng) - in this code, its just an integer as a seed value in LHS.
        # Start with 7 uniform budget configs as initial points (anchors for the Pareto front)
        # BUDGET_OPTIONS = [64, 128, 256, 512, 1024, 2048, 4096]
        # Mapping: x in [0,1] → budget_idx = int(x * 7) → BUDGET_OPTIONS[budget_idx]
        # Using center of each bin to avoid floating-point edge cases:
        # These are placed FIRST so they are evaluated first (configs 1-7)
        if int(os.environ.get("NAS_TARGET_BUDGET", "0")) > 0:
            # Fixed-budget-slice mode: the mean budget is pinned, so any
            # CONSTANT vector decodes to the same uniform allocation — the 7
            # uniform anchors would be duplicates. Seed allocation SHAPES
            # instead (heuristic controls); LHS remainder below is the
            # random-allocation control.
            ramp = np.linspace(0.05, 0.95, 32)
            tri = np.concatenate([np.linspace(0.05, 0.95, 16), np.linspace(0.95, 0.05, 16)])
            shape_configs = [
                [0.5] * 32,                    # uniform at the target budget
                list(ramp),                    # ascending ramp (late layers heavy)
                list(ramp[::-1]),              # descending ramp (early layers heavy)
                list(tri),                     # middle-heavy triangle
                list(1.0 - tri),               # edge-heavy inverse triangle
                [0.15, 0.85] * 16,             # alternating low/high
            ]
            anchor_file = os.environ.get("NAS_ANCHOR_FILE", "")
            if anchor_file and os.path.isfile(anchor_file):
                # Seed a known-good allocation shape: budgets → normalized weights
                b = np.loadtxt(anchor_file).reshape(-1)[:32]
                shape_configs.append(list(0.05 + 0.9 * (b / b.max())))
                print(f"Seeded anchor shape from {anchor_file}")
            else:
                shape_configs.append([0.35, 0.65] * 16)  # second alternating shape
            X_init = np.array(shape_configs, dtype=float)  # 7 x D array
            print("Slice mode: 7 shape anchors (uniform/ramps/triangles/alt/winner)")
        else:
            uniform_configs = [
                [0.071] * 32,  # ALL 64   — minimum budget baseline
                [0.214] * 32,  # ALL 128  — low budget baseline
                [0.357] * 32,  # ALL 256  — medium-low budget baseline
                [0.500] * 32,  # ALL 512  — medium budget baseline
                [0.643] * 32,  # ALL 1024 — medium-high budget baseline
                [0.786] * 32,  # ALL 2048 — high budget baseline
                [0.929] * 32,  # ALL 4096 — maximum budget baseline
            ]
            X_init = np.array(uniform_configs, dtype=float)  # 7 x D array
        
        # Append N-7 LHS points after the uniform configs
        sampler = qmc.LatinHypercube(D, seed = rng) # D dimensional LHS. With a different seed in every simulation to create the statistics. 
        X_lhs = sampler.random(N - 7) # N-7 LHS points
        X_init = np.vstack((X_init, X_lhs))
        print("Initial points (7 uniform budget anchors + LHS)")
        f_init = HFF_mod.call_HFF(X_init) # Obtain the high fidelity objectives in f_init: N x M

        HFF_D_set = np.zeros((N,D+M)) # Database of high fidelity calls - needed for book-keeping
        for i in range(N):
            HFF_D_set[i,0:D] = np.copy(X_init[i,:])
            HFF_D_set[i,D:D+M] = np.copy(f_init[i,0:M])
                
        print('Iteration number 0 completed | Repetition:', n_repeat+1)
        if M <= 3:
            plot_pareto(HFF_D_set, M, true_front_flag, 0, HFF_counter)

        for n_iter in range(num_iter): # BO loop
            if (n_iter+1) % N_switch != 0:
                # Step 2a: Training data generation for classifier (ANN) for Rank 1
                obt_front, rnk1idx = ndsort.rank_one(np.copy(HFF_D_set[:,D:D+M]))
                rnk1pts = np.size(obt_front, 0)
                print('Number of Rank 1 points = ', rnk1pts)

                ANN_D_set = call_TDG(HFF_D_set, rnk1idx, M) 
                # N D+M dimensional data points go in as input and N D+1 dimensional data points comes out as output from this code
                # Inputs remain same. Outputs get changed. Instead of continuous outputs we have binary labels.
                # D+1 dimensions because D are original inputs, and 1 is label.  
                
                # Step 3a: Train the classifier (ANN)
                NN_clf_rnk1 = call_train_NN(ANN_D_set)

                # Step 4a: Optimize
                x_bounds = [] 
                # I have to find a new point in 0 to 1 scale because the NN trains everything in 0 to 1 scale. 
                # So I dont have to worry about real bounds here. 
                for i in range(D): # D because D is input dimensions and we have inputs as the decision variables. 
                    x_bounds = x_bounds + [[0,1]] # Lower bound and Upper bound

                # Differential Evolution (de) as optimizer
                ACF_result = de(call_NN_ACF_obj, bounds = x_bounds, args = (NN_clf_rnk1,))
                X_new = ACF_result['x']
                X_new = X_new.reshape(1,D)
                flag = 1 # Counter for new HFF
            else:
                # Step 2b: Training data generation for classifier (ANN) for each objective
                clf_list = []
                for i in range(M):
                    ANN_D_set = call_TDG1(HFF_D_set,M,gamma,i) 
                    # N D+M dimensional data points go in as input and N D+1 dimensional data points comes out as output from this code
                    # Inputs remain same. Outputs get changed. Instead of continuous outputs we have binary labels.
                    # D+1 dimensions because D are original inputs, and 1 is label.  
                
                    # Step 3b: Train the classifier (ANN)
                    NN_clf = call_train_NN(ANN_D_set)
                    clf_list = clf_list + [NN_clf]
                
                # Step 4b: Find the new points
                N_points = 10000
                uni_sampler = qmc.Sobol(d=D) # uniform sampling using Sobol
                X_points = uni_sampler.random(N_points) # returns a matrix of size N_points x D

                # Evaluate the class 0 probabilities for all objectives by running across all clf
                pop_fit = np.empty([N_points,M])       
                for i in range(M):
                    Y_pred_proba = clf_list[i].predict_proba(X_points)
                    pop_fit[:,i] = Y_pred_proba[:,0] # Interested in Class 0 probabilities only. 
                # Filter any point that minimizes any objective 
                flag = 0
                for i in range(N_points):
                    for j in range(M):
                        if pop_fit[i,j] >= 0.9999:
                            flag = flag + 1
                            break
                    if flag == 1:
                        X_new = np.reshape(np.copy(X_points[i,:]),(1,D))
                    else:
                        X_new = np.vstack((X_new,X_points[i,:]))
                X_new = X_points
            
            # Step 5: High fidelity function call
            if flag != 0:
                HFF_counter = HFF_counter + flag        
                f_new = HFF_mod.call_HFF(X_new) # Obtain the high fidelity objectives in f_init: Some points x M           
                HFF_D = np.zeros((flag,D+M)) # To update the Database of high fidelity calls - needed for book-keeping
                for i in range(flag):
                    HFF_D[i,0:D] = np.copy(X_new[i,:])
                    HFF_D[i,D:D+M] = np.copy(f_new[i,0:M])
                HFF_D_set = np.vstack((HFF_D_set,HFF_D)) # Appending to the HFF database
                print('Iteration number', n_iter+1, 'completed | HFF Calls:', HFF_counter, '| Repetition:',n_repeat+1,)
                if M <= 3:
                    plot_pareto(HFF_D_set, M, true_front_flag, n_iter, HFF_counter)
            else:
                print('Iteration number', n_iter+1, 'failed | HFF Calls:', HFF_counter, '| Repetition:',n_repeat+1,)

    # ─── Total search time summary ────────────────────────────────────────────
    total_search_elapsed = time.time() - total_search_start
    hrs = int(total_search_elapsed // 3600)
    mins = int((total_search_elapsed % 3600) // 60)
    secs = total_search_elapsed % 60
    print(f"\n{'='*60}")
    print(f"TOTAL NAS SEARCH TIME: {hrs}h {mins}m {secs:.1f}s ({total_search_elapsed:.1f}s)")
    print(f"Total HFF calls: {HFF_counter}")
    print(f"Avg time per config: {total_search_elapsed/HFF_counter:.1f}s")
    print(f"{'='*60}")
