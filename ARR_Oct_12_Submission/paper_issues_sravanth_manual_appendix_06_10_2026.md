A Per-Cell Results

1. "RULER uses its 11 subtasks" -> give the 11 substasks aswell, similar to longbench 

2. In Table 5, remove the floor thing and for all tasks keep one task in the center keep the { to the right of it.

3. If Table 5, Table 6 are for Meta Llama; then are also keeping for Mistral?

4. In Table 5, Table 6 -> Thats boring give me different way of representations for it.

5. Table 13, its also similar to Table 5,6 right?

=== done till now ====


I have some concerns regarding the section c of the appendix:

Narrative: The main key of ours vs evolkv is we take more data samples in calibration than tha evolkc which take only 30 samples, but evolkv takes more number of evols to run, this can give us almost same of gpu hours compare to evolkv and even lesser in some cases. The only thing is that we need to search 2 times for every budget/eviction method, whereas the evolkv will be doing it only once. 

Table 11 -> Lets keep that MOSAIC runs on 10% calib dataset, and had 150 max evals.

So please remove the watchdog and 200-evaluation cap and allm those things in the text referring to Table 11

Table 12 & text supporting it -> I am not able to understand it, can you make it simpler, will this follow our narrative.


==========================

In section E, I've some concerns

"SnapKV and H2O always retain an 8-token recent 706
window, so a layer with budget b selects only b − 8 707
tokens by attention (Table 14)." -> sentence is fine, table is uncessary, please delete it.

Also give me better representation of Table 15, that looks odd. 

"under the earlier floor of 16, up to two-thirds of 712
layers sat there (RULER B1024, H2O), while at 713
B1536 and B2048 no layer did, so those cells are 714
floor-independent" -> this is unnecessary, please delete it


"Figure 7 shows the floor- 716
16 RULER B1024 SnapKV configurations, which 717
park many layers at 16." -> this is also not required i think, remove the text and figure, what do you think

"Controlled comparison. Table 16 decodes the
720 same rescaled SnapKV winner under both floors
721 and evaluates both on full data. Floor 64 is better
722 in three cells, all at B128 (by 0.37–1.10 points), the
723 two are tied in two cells, and floor 16 is better in
724 one (by 0.26). The differences concentrate at the
725 lowest budget, where the floor binds most often." -> this is obvious right and table 16 as well. 