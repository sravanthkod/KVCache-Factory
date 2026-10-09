# Non-Dom sorting code: Approach 2 in NSGA-II book by K.Deb
# Coded by Srinivas S Miriyala on 10-8-22
import numpy as np

def ndsort(func,ret):
    fitness_matrix = np.copy(func) 
    # input is a matrix of size n x m, n = number of candidates and m = number of objectives
    # another input is integer ret: if 1 will return the ranks of each pop, if 0 will return the fronts.
    # returns a list called fronts where each entry will be Pareto fronts arranged as per the ranking
    fronts = [] 
    P, rank1index = rank_one(fitness_matrix)
    ranks = np.copy(rank1index)
    fronts = fronts + [P]
    #print('Rank 1 :\n', P)
    rnk = 1
    while sum(rank1index) != len(rank1index):
        rnk += 1
        delidx = []
        for i in range(np.size(fitness_matrix,0)):
            if rank1index[i] == 1:
                delidx = delidx + [i] 
        fitness_matrix = np.delete(fitness_matrix,delidx,0)
        P, rank1index = rank_one(fitness_matrix)
        fronts = fronts + [P]
        #print('Rank', rnk, ':\n', P)

    if ret == 0:    
        return fronts
    else:
        for k in range(1, len(fronts)):
            pop = fronts[k]
            for i in range(np.size(pop,0)):
                for j in range(np.size(func,0)):
                    if sum(pop[i,:] == func[j,:]) == np.size(func,1):
                        ranks[j] = k+1
                        break
        return ranks

def rank_one(pop_fitness):
    # input is pop_fitness is a matrix of size n x m, n = number of pop and m = number of obj
    # returns a subset of pop_fitness that is rank1 and also the vector of indices in pop_fitness that are rank1
    popsize = np.size(pop_fitness,0)
    nfunc = np.size(pop_fitness,1)

    P = np.copy(pop_fitness[0,:]).reshape((1,nfunc)) # Rank 1 front - initially set = first element in the pop - will be updated
    rank1index = np.zeros(popsize) # This is a vector of size = popsize: if entry is 1, corresponding index is Rank 1.
    rank1index[0] = 1 # 1st entry is entered in P, thus 1st entry in rank1index is 1
    rank1size = np.size(P,0) # size of Rank 1 pop i.e. P front
    remove_pop = np.zeros(rank1size) # counter for updating P

    for i in range(1,popsize): # Loop for all pop except first element in the pop
        # Actions of ith pop on P
        for j in range(rank1size): # Loop for P
            # Compare i with j
            flag = compare_fitness(pop_fitness[i,:],P[j,:])                   
            if flag == 1: # if i dominates j: delete j, update enter_i, continue j loop
                remove_pop[j] = 1
            elif flag == 2: # if j dominates i: exit out of j loop and check another i             
                break

        # Update the P now based on the actions of ith pop
        if flag != 2: # If flag is 2, i is useless and so no change needed in P. 
            # Since flag is not 2, i will enter the P.
            # Because there is no possible way where i will dominate a member of P and then gets dominated by another point in P
            # So if i is dominating a point in P, then it can either dominate all members of P or 
            # domainate some more members of P and be non-dom with remaining members of P.
            # So First delete entries from P and then append i in P. 
            if sum(remove_pop) != 0: 
                # if sum(remove_pop) is 0, nothing needs to be removed from P
                delidx = []
                for j in range(rank1size): # update the rank1index and P
                    if(remove_pop[j] == 1): 
                        delidx = delidx + [j] # Collect all indices that need to be deleted from P
                        # Whatever I am deleting from P, I need to remove that index from rank1index list. 
                        for k in range(i): # this loop is for modifying the rank1index
                            # I have to remove existing points in P. 
                            # We are going in ascending order of indices of pop_fitness using the i loop. 
                            # We are checking if i will go into P or not. 
                            # So whatever is in P, its index will be < the current i in pop_fitness matrix. 
                            # Thus range(i). 
                            if sum(pop_fitness[k,:] == P[j,:]) == nfunc: # Compare if the pop is same as that in P
                                rank1index[k] = 0 # Removing the index
                                break # We dont need the k loop anymore. 
                P = np.delete(P,delidx,0) # Modify the P 
            # Add i to P and update it in rank1index
            P = np.vstack((P,pop_fitness[i,:]))
            rank1index[i] = 1
            rank1size = np.size(P,0)
            remove_pop = np.zeros(rank1size)
    return P,rank1index

def compare_fitness(pop1_fit, pop2_fit):
    # inputs pop1_fit and pop2_fit are vectors of fitnesses for pop1 and pop2
    # returns a indicator for dominating, dominated or non-dominating
    dom = 3 # pop1 and pop2 are non-dominating
    if sum(pop1_fit <= pop2_fit) == len(pop1_fit):
        dom = 1 # pop1 is dominating
    elif sum(pop1_fit >= pop2_fit) == len(pop1_fit):
        dom = 2 # pop2 is dominating
    return dom

#a = np.array([[1.,2.],[5.,5.],[4.,3.],[2.,1.],[3.,4.],[1.5,1.5],[0.5,2.5],[2.5,1]])
#fronts = ndsort(a)    
#print(fronts) 
