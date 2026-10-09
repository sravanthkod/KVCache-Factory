0. Abstract:
 I dont want to keep the negative things like 63/67 and four losses are small in abstract, since the abstract is the first view of the paper, dont want to make an underestimted view of the paper here. Same for 68/78 and unreliability on Longbench and 17/48 aswell.


1. Introduction:

"MOSAIC searches the 32- 069
dimensional per-layer budget space" -> here 32 is number of layers in the model, we dont always do the 32 search, we do search for all layers in the model. 

"We evaluate MOSAIC across four eviction methods (SnapKV, H2O, AdaKV, L2Norm)" -> here adakv is not introduced before, add some intro for it before writing what we are doing. 

"On LongBench, gains are smaller: every Code cell 080
improves, QA shows four small losses, and some 081
datasets drop even where the category mean im- 082
proves." -> this negative statments need a good writeup.

"MOSAIC versus EvolKV" -> before ever starting this thing, better to add some intro to evolkv. 

"layer budgets block by block (groups of 8, earlier
087 groups frozen) at one fixed budget on 30 calibration
088 samples, then extrapolates." -> here also write what search does evolkv uses. 

"(i) it searches all 32 budgets jointly," -> here again number of layers.

"one unconstrained search explores the budget" -> explain unconstrained here, readers will be confused here

"it selects by full-data rather than
099 calibration scores, which on LongBench misrank
100 configurations and overstate EvolKV’s own scores
101 by 6.7–9.8 points." -> write this in a better way

"across budgets (it beats uniform in 68/78
116 cells on the evaluated examples);" -> 68/78 is not required here in thr introduction section

"evidence that
117 calibration-subsample scores do not reliably rank
118 configurations on LongBench, motivating full-data
119 selection; and " -> if we tell for longbench, then the calib % should differ from longbench and ruler right, but we kept the same for ruler and longbench, any issue for this?

"allocations,
which favour a small set of middle layers 120
(10, 14–16, 18 and 20)." -> these numbers are not required. 

Also Figure 1 is not being cited anywhere, please check this.

2. Related Work:

"Budget allocation. A second line of work" -> can we give dynamic bugdet allocation here. 

Also add the state of the art papers like KeyDiff and QuoKA  -

Keydiff -  https://arxiv.org/pdf/2504.15364
QuoKA  - https://arxiv.org/pdf/2602.08722v1


3. Method:

3.1 Problem Formulation:

"so at budget 16 a layer selects
171 only 8 tokens by attention, a degenerate regime
172 an earlier floor of 16 let the search exploit." -> why are we explaining this?

3.2 Search Procedure (MOSAIC— Four-Stage Pipeline):

In the pipeline, also clearly mention that we made this 4 stage because, when we get a configuration in search from stage 1, we cant compare it uniform budget since this config will arbitary budget. thats led us into the 4 stage method, also one can stop after doing step 3, step 4 aim is to even go search for a better config than the one already found in previous steps. So, one can stop after step 3 aswell.

"RULER, for L2Norm and for H2O Code" -> this should be for RULER, not mention about eviction algorithms here

"whole budget range, and runs only once per 209
(task, method), it uses a larger calibration subsam- 210
ple on LongBench (30%)." -> what about RULER?

"Pareto front (13–17 configurations per category 214
for AdaKV)" -> dont mention like this, give a rough number and dont keep adakv here. 

"Two exceptions, AdaKV 217
on LongBench and H2O on RULER, took the 218
best-calibration configuration instead (see Limita- 219
tions)" -> remove this

"Stage
4 calibration subsample: 10%." -> why did we keep this in Table 1, its not required.

Also we directly we into in table 1,2 -> mention in detail that we took four usecases in longbench those are code, summ, single doc, multi doc and each again contains different datasets in it. 

"For each target budget B, perform
243 a dedicated BO search constrained to produce
244 configurations with average budget exactly B." -> I need specifics here, similar to the way we formulated in the problem formulation section

"run lengths varied from
254 97 to 1000 evaluations across methods and" -> this 97 to 1000 looks awkward, please change this.

"RULER uses 10% in
259 both stages:" -> specifically write stage 1, 4

"The calibration-best heuristic shape, LHS point
262 and guided proposal are re-evaluated on full data and the best is reported as NAS-refined" -> dont mention all these, just tell the best config from search 4 Wis called as NAS-refined

"It is a 268
guided proposal in only 25 of the 67 cells; in the 269
others it is the rescaled Winner (19) or a heuristic 270
or LHS point from the initial design (23), so the 271
result comes from the workflow, not from guided 272
search alone." -> don't ever mention abt these since I dont want to tell explicitly that result comes from workflow, instead we can tell that stage 4 doesn't gaurantee always improvement over stage 2 - winner, in some cases we found improvement, mix the 23 + 25 = 48 for stage 4 > stage 2, for 19 cases, its stage 2> stage 4, in this way.

"Selection and evaluation data." -> here mention clearly about the data split and usecases in it. 
