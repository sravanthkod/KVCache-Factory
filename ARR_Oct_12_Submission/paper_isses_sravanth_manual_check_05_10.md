
One rule, I want you to follow is, dont ever explictly mention negatively that results are very near to uniform and all those negative things in the initial sections of paper, because those are the first sections checked by the reviewers and others, I want to have positive influence of the paper in the initial sections, saying that MOSAIC improves the uniform allocation.

You can also mention that MOSAIC is a kind of static quantization scheme where we are finding the budget allocation needed for each model layer on the calibration dataset, which is very similar to static quantization where we find the scale and zero points on the calibration datasets, where as the methods like cakekv,pyramidkv measures the dynamicness of the budgets as per input prompts, which is similar to dynamic quantization. -> You can also add this kind of explanation aswell in the paper. 

0. Abstract

"selects a winner by
017 full-data evaluation" -> this is not required 

"rescales it to any target
018 budget, and optionally refines each budget with
019 a budget-constrained search." -> instead of this explanation, please keep it like MOSAIC brings 4 step evaluation method where one can search with budget constrains, better to keep in that style

"consistent
023 gains on LongBench Code." -> mention this as longbench and give the delta value over uniform here, choose the delta value where we had the biggest difference, also dont go for average scores directly, you can check any dataset scores as well. 

"onfigurations are selected and scored on the
028 benchmark examples; held-out evaluation is
029 left to future work." -> this is confusing, why we tell future work in the abstract itself, change this.

1. Introduction

"On LongBench, where the evidence is spread over 075
long documents, gains are smaller:" -> dont mention this, Instead of getting average score give any dataset specific score in longbench i.e. dataset in single doc, multi doc etc where we had large positive delta than uniform,

"and otherwise stays within a point of 078
uniform" -> dont mention this

"MOSAIC applies it to KV-cache allocation,
169 treating each layer’s budget as an architecture pa170
rameter." -> when we tell this, its like direct implementation with no novely, our optmization algorithm is not from any opensource algorithm, this algorithm is novel and ours will be done in low cost budget.

3. Method

"so it uses a smaller 287
subsample (10% on LongBench) to keep its 288
per-budget cost comparable to EvolKV’s." -> if we write in this way then the question comes is why 30% in stage 1, also if we tell to be comparable with evolkv we did 10% its wont look right.

Also mention that we had performed the search seperately on single doc, multi doc, code, summarization due to their different accuracy evaluations , but coming to RULER holding 11 datasets, we performed a single search across entire ruler.


4. Experiments

"Budgets: 64–2048 average tokens per
335 layer." -> here 16/64 ad minimum and 1024/2048/4096 as max right, are we sure on this?

"Experiments ran on four servers with A100, RTX
342 A6000 and H100 GPUs." -> lets keep A100 only