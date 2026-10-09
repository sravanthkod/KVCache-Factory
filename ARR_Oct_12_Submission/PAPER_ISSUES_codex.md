# MOSAIC paper review: issues to address before ARR submission

Review date: 2026-10-08  
Paper: *MOSAIC: Multi-Objective Search for Allocating Inference Cache Across LLM Decoder Layers*  
Reviewed version: [main.pdf](acl-style-files-master/main.pdf), 26 pages; PDF creation/modification time 2026-10-08 16:37:03 UTC.  
Scope: compared the complete extracted current PDF against the October 8 16:26:12 version. The substantive changes are in Appendix H's candidate-provenance definition and Algorithm 1's shortlist rule; the rest of the textual diff is associated layout/line-number changes. This update is a manuscript review, not an implementation or experiment audit. Paper/source files were not edited. The current assessment is immediately below; subsequent dated assessments and the reference audit refer to their explicitly identified earlier PDFs.

## Current assessment — October 8, 16:37:03 PDF

**Overall remains 3/5 — Findings-level recommendation.** Soundness 3.5/5, excitement 4/5, reproducibility 3/5, confidence 4/5, on the same hypothetical scales as the previous reviews. This revision resolves a specific manuscript inconsistency; it does not introduce new experiments or change the reported gains.

### Concern now resolved: NAS-refined versus Winner

Appendix H, lines 949–956, now explicitly distinguishes uniform and Winner from the other search candidates (heuristic shapes, LHS points and guided proposals). NAS-refined is chosen from the latter group, excludes uniform and Winner, and can therefore score below Winner. Algorithm 1, line 9, now takes the calibration-best shortlist from `A_B \ {uniform, b_W}`; line 11 separately compares NAS-refined with Winner on full data.

**Close the earlier objection that the NAS-refined definition mathematically contradicts Winner outperforming it in 24/78 Llama cells.** The distinction between seeds, shortlisted alternative configurations and final output is now clear and consistent with that observation. This is a genuine clarity improvement. It verifies the manuscript's definition, not that every historical run followed it; no implementation audit was performed.

### Remaining concerns and rating rationale

- **Independent evaluation is still absent:** full-data selection and reporting on the same examples remain explicitly described in Section 3.2. Correcting the candidate definition does not remove selection dependence.
- **Equal-budget optimizer control is still absent:** initial LHS seeds do not substitute for a full random/LHS search with the same total evaluations and selection rules.
- **Abstract efficiency/search-space qualifications remain unchanged:** the 18% saving is aggregate incremental Stage 4 cost, excluding Stages 1–2; the roughly 10^40 ratio is a joint-versus-one-group proposal-domain comparison, not measured exploration volume.
- **The shortened Limitations section still omits substantive unresolved caveats** identified in the preceding review. Restore the evaluation, total-cost and optimizer-control limitations.
- **Reproducibility details still need completion.** Specify shortlist size/ranking and the identity/count of candidates charged to Table 15's full-data re-evaluation, exact rounding/tie rules and run-prefix provenance. This is a narrower documentation request, not a reason to reopen the now-resolved NAS-refined-versus-Winner contradiction.

The reported results remain 74/78 Llama and 72/76 Mistral, or 146/154 combined. With one wording inconsistency closed and the evidence limitations otherwise unchanged, the overall recommendation remains Findings-level rather than a main-conference-level recommendation. No acceptance guarantee is implied.

## Historical assessment — October 8, 16:26:12 PDF

**Overall: 3/5 — Findings-level recommendation, unchanged.** Soundness 3.5/5, excitement 4/5, reproducibility 3/5, confidence 4/5. These are the same hypothetical reviewer scales used in the preceding reviews, not acceptance probabilities or a claim that every ARR cycle uses exactly this form. The paper's practical idea, broad evaluation and interpretable allocations remain strengths. The new reference corrections improve presentation and positioning, but the headline results remain 74/78 Llama and 72/76 Mistral (146/154 combined), with no newly reported independent evaluation or equal-budget unguided-search control. I therefore would not raise the overall recommendation to a main-conference-level rating on these edits alone.

### Improvements credited in this version

- **PyramidKV's bibliography is corrected.** The compiled reference now includes Yuliang Liu and Yucheng Li, bringing the author list to eleven. Close that metadata issue from the reference audit below.
- **The introduction no longer claims prior allocation schemes overlook layer heterogeneity.** Lines 53–55 explicitly acknowledge that they already exploit layer differences and state MOSAIC's joint-search distinction. Close the inaccurate novelty-transition objection.
- **The quantization citation is better scoped.** Lines 71–73 now describe offline calibration in post-training quantization, rather than attributing a specific static-scale/zero-point mechanism to GPTQ. Credit the broader analogy; the remaining claim that MOSAIC fixes budgets “on calibration data” still omits its full-data selection step.
- **PyramidInfer's mechanism is described more accurately.** Lines 161–163 now refer to context consistently selected by attention and decreasing retention with depth. The earlier implication that it uses the same hand-designed integer budget schedule as PyramidKV is reduced. However, it remains grouped under methods that “fix the allocation before inference”; distinguish a fixed policy from prompt-dependent retained contexts/counts.
- **EvolKV expansion remains explicitly acknowledged** in Related Work and Section 6. Do not reopen the old incorrect claim that EvolKV must search again at every target budget.

### Main reasons the rating does not increase

1. **Selection-dependent evaluation is unchanged.** Section 3.2, lines 328–339, explicitly says Stages 2 and 4 select on full task data and all reported scores use that same data. It correctly restricts the evidence to gains on evaluated examples rather than unseen-example generalization. A Stage 3 allocation can be frozen at inference while still inheriting Stage 2's dependence on the reporting examples. This is an evaluation-design issue, not a failure to explain the pipeline. More references do not change it.

2. **The guided optimizer's incremental benefit remains unisolated.** Appendix H still includes 57 LHS points in the 64-point initial design. This is useful seed-level evidence, but it does not compare a complete guided search with an equally long random/LHS search using the same data and selection rule. Good seed or heuristic results can support the complete MOSAIC workflow without establishing that guidance adds value. No new same-budget unguided control, repeated-search uncertainty or measured inference latency/throughput result was found in this version.

3. **NAS-refined's definition still conflicts across passages.** Algorithm 1 takes the calibration-best shortlist C, selects bN from C on full data, and then separately compares bN with the Winner. That is compatible with Table 1's Winner being better than NAS-refined in 24/78 Llama cells. But Appendix H, lines 949–952, says Stage 4 re-evaluates uniform, Winner and calibration-best candidates and calls the best of these NAS-refined. That definition would make NAS-refined never worse than Winner or uniform. Define C explicitly and distinguish shortlist selection from the final comparison. Uniform/Winner being initial search seeds does not imply they are automatically shortlisted at the end. Table 15's three re-evaluated candidates also needs an exact consistent definition.

4. **Headline efficiency claims remain more sweeping than the accounting.** The abstract still says “18% fewer GPU-hours per budget,” while Table 15 reports an aggregate Stage 4 saving: 43.8 versus 53.7 GPU-hours across six cells, excluding Stages 1–2. Appendix D still gives end-to-end costs of at least 43.1 + 21.2 = 64.3 GPU-hours versus 38.3 + 15.4 = 53.7. Say “18% lower aggregate refinement cost across six cells, excluding one-time search/selection,” not an unqualified whole-workflow saving. The 9–40 GPU-hour range is selected Stage 1 cost, not the complete cost of selecting a deployable anchor. MOSAIC and EvolKV also use different sample counts (55–100 versus 30 per search evaluation), so distinguish a workflow cost comparison from an optimizer-only comparison.

5. **The search-space ratio is a proposal-domain comparison, not exploration volume.** The abstract still says MOSAIC “explores” a roughly 10^40-times larger space. The derivation compares all-layer fixed-budget allocations with one eight-layer EvolKV optimization phase; a complete EvolKV run optimizes multiple groups and both methods' outputs occupy the same global bounded allocation domain. MOSAIC actually evaluates only a small number of configurations. Prefer “jointly optimizes all layers rather than one group at a time” and retain any clearly qualified combinatorial comparison in the appendix.

### Important regression: shortened Limitations

The former Limitations section explicitly acknowledged same-example selection/evaluation, end-to-end search cost, uneven settings and the absence of an equal-cost random-search comparison. The current “Limitations and Future Work” section, lines 500–513, retains model/summarization scope and proposed future architectures/methods but removes those substantive caveats. They have not been experimentally resolved. Some remain disclosed elsewhere, especially the selection issue in Section 3.2 and costs in Appendix D, but removing them from Limitations weakens the summary of the work's boundaries.

**Restore a short paragraph covering:** no independent frozen-allocation test; no equal-cost random/LHS search control or repeated-search uncertainty; ideal KV-budget savings rather than measured inference memory/latency/throughput; total workflow cost including one-time search/selection; and protocol exceptions. These are limitations of the present evidence, not merely plans to try newer model families. This is a transparency concern, not a prediction of automatic desk rejection.

### Remaining writing/reproducibility fixes

- **Separate matched-budget wins from cross-budget cache savings.** The conclusion compresses “146/154” and “up to 4× less KV cache” into one sentence. The win count concerns comparison at the same average budget; the cache-saving claim uses a smaller MOSAIC budget versus a larger uniform budget. Report these separately and list the pairs/selection rule supporting the fourfold and 17-setting claims. Ideal KV payload reduction is not measured total GPU memory reduction.
- **Calibration scope is inconsistent.** Section 4.1 specifies 30% for all Mistral LongBench and L2Norm searches, while Section 3.2's Stage 4 explanation says 10% on both benchmarks without these exceptions. State the exceptions alongside the general rule. Setup's floor-16 qualification also still refers only to earlier RULER runs despite Table 7 documenting floor-16 Mistral LongBench runs.
- **Complete the rescaling/rounding specification.** Appendix H describes clamping, proportional redistribution and rounding to the exact total, which is meaningful progress relative to early drafts. Exact residual allocation/tie-breaking and zero-weight handling remain unspecified. Avoid reopening the broader obsolete objection that no rescaling procedure is provided. Add settings/artifacts for decoding, sampling seed, surrogate/DE defaults and per-experiment hardware.
- **Clarify search-prefix provenance.** Appendix D still retains the first at-most-150 evaluations of historical Stage 4 runs. Identify which candidates were selected using only that prefix and whether carried anchors came from the declared Stage 1 cap. Section 3.2's “180/150” phrasing for Stage 4 is ambiguous compared with Appendix H's Stage 1=180, Stage 4=150. This needs a provenance table or precise wording, not an assumed implementation error.
- Remaining reference-wording issues from the historical audit include the H2O “as do” sentence, QUOKA/QUEST eviction-versus-access distinction, untested composability, and the categorical DARTS exclusion. BORE is a legitimate related citation; make its Pareto-label extension explicit if space permits.

**Bottom line:** better referenced and better positioned, but not stronger experimental evidence in this update. I remain at 3/5, with Findings as my hypothetical recommendation rather than main-track acceptance. The fastest writing-only improvements are restoring substantive limitations, reconciling NAS-refined's definition, and qualifying abstract cost/search-space claims. Independent evaluation and a matched-budget search control would be substantive reasons to revisit the overall score.

## Reference authenticity, relevance and wording audit — October 8, 15:41:44 PDF

Scope: audited the 36 references actually compiled into the updated 26-page PDF, using the PDF, compiled bibliography and primary publication records/papers. Unused entries in bibliography files are outside this audit. This is a focused reference audit, not a new full-paper rating; the full-paper assessment below remains tied to the 15:08:58 version. No paper, TeX or bibliography files were edited. Publication identity/metadata was checked for all entries; method descriptions were checked against the relevant source abstracts and selected passages/algorithms, not by rereading every cited paper end to end. Some publisher/OpenReview pages restrict direct access; indexed primary records and author-hosted papers were used where necessary.

### Bottom line

**All 36 compiled references identify real works; I found no hallucinated paper identities.** They are relevant overall. The important corrections are one incomplete author list and several citation-to-claim mismatches. A real citation does not automatically support every sentence attached to it.

### Required bibliographic correction

**PyramidKV (Cai et al., 2025): the author list is incomplete for the cited COLM 2025 version.** The current entry lists nine authors. The [official COLM accepted-paper record](https://colmweb.org/2025/AcceptedPapers.html) and [conference paper](https://openreview.net/pdf?id=ayi7qezU87) list eleven: Zefan Cai, Yichi Zhang, Bofei Gao, **Yuliang Liu, Yucheng Li**, Tianyu Liu, Keming Lu, Wayne Xiong, Yue Dong, Junjie Hu and Wen Xiao. Add the two missing authors in this order. The paper and COLM 2025 venue are real; this is incomplete metadata, not a fabricated reference.

### Wording corrections, in priority order

1. **Separate PyramidInfer from PyramidKV's fixed budget schedule.** Section 2, approximately lines 157–162, places PyramidInfer alongside PyramidKV under a static per-layer-budget description. [PyramidInfer](https://aclanthology.org/2024.findings-acl.195/) progressively retains pivotal contexts using attention consistency and layer-dependent compression. Its algorithm applies attention-based top-p selection; this is not simply the same fixed integer budget vector as PyramidKV. Suggested wording: “PyramidKV uses a pyramidal layer-budget schedule, while PyramidInfer progressively compresses layerwise pivotal contexts using attention-based selection.” A fixed compression policy and fixed retained-token counts are different concepts. Keep both citations, but describe their mechanisms separately.

2. **Broaden or qualify the static-quantization analogy.** Introduction, lines 69–78, cites SmoothQuant and GPTQ for static calibration of scales/zero points. [GPTQ](https://arxiv.org/abs/2210.17323) is specifically one-shot **weight** quantization; it is not an appropriate exemplar of fixed activation-scale calibration. [SmoothQuant](https://proceedings.mlr.press/v202/xiao23c.html) uses offline calibration and supports multiple quantization variants, so avoid implying all variants have identical static activation quantization. Suggested wording: “Analogous to offline calibration in post-training quantization, MOSAIC determines a reusable layer-budget allocation before deployment.” Both citations can support this broader analogy. Also replace “fixes each layer's budget offline on calibration data” with “searches on calibration data and selects a reusable allocation offline”: the current pipeline explicitly also uses full task data for selection. This is about accurately describing the manuscript's protocol, not denying that inference-time allocation is frozen.

3. **Do not say layer-budget prior work overlooks layer heterogeneity.** The introductory transition around lines 51–54 cites PyramidKV, CAKE and EvolKV before claiming that existing approaches overlook differing layer priorities. These works explicitly exploit layerwise heterogeneity. [CAKE](https://openreview.net/pdf/b1d9910c4ac08cd3ef1dfd4459a1f3196028444c.pdf), [PyramidKV](https://openreview.net/pdf?id=ayi7qezU87) and [EvolKV](https://aclanthology.org/2025.findings-emnlp.88/) are relevant prior art, not evidence that this idea was previously overlooked. Suggested transition: “These methods exploit layer heterogeneity but differ in how they derive allocations. MOSAIC jointly searches layer budgets across a budget–score trade-off and transfers a selected allocation to deployment budgets.” Any novelty claim should concern the demonstrated workflow/search distinction, not discovering heterogeneity itself.

4. **Distinguish token eviction from sparse attention access.** QUOKA and KeyDiff are real and relevant, but their inclusion should not imply that every cited method permanently discards cache entries. [QUOKA](https://arxiv.org/abs/2602.08722) selects representative queries and associated keys for sparse prefill attention. Describe this as reducing attention participation/work, rather than automatically equating it with persistent KV-cache eviction. Appendix G correctly says [QUEST](https://proceedings.mlr.press/v235/tang24l.html) retains the full cache and accesses relevant pages, but the lead-in saying all these techniques “shrink the KV cache” conflicts with that distinction. Suggested lead-in: “Complementary inference-efficiency methods reduce attention access, storage precision or cross-layer redundancy.”

5. **Unpack the H2O/StreamingLLM/Scissorhands/FastGen sentence.** Section 2, lines 123–128, uses “as do” after H2O's heavy-hitter-plus-recent-window description. This can misleadingly attribute the same rule to all three subsequent methods. Suggested wording: “H2O retains accumulated-attention heavy hitters and recent tokens; StreamingLLM retains initial attention-sink tokens and a recent window; Scissorhands exploits persistence of token importance; FastGen profiles attention heads to choose head-specific compression policies.” The references themselves are appropriate: [H2O](https://proceedings.neurips.cc/paper_files/paper/2023/hash/6ceefa7b15572587b78ecfcebb2827f8-Abstract-Conference.html), [StreamingLLM](https://arxiv.org/abs/2309.17453), [Scissorhands](https://proceedings.neurips.cc/paper_files/paper/2023/hash/a452a7c6c463e4ae8fbdc614c6e983e6-Abstract-Conference.html), [FastGen](https://openreview.net/pdf?id=uNrFpDPMyo).

6. **Make the BORE relationship precise without claiming identical optimization.** Section 3's classifier-guided search citation to [Tiao et al. (2021), BORE](https://proceedings.mlr.press/v139/tiao21a.html), is relevant and legitimate. BORE constructs classification labels using an objective quantile; MOSAIC uses Pareto-rank labels. Suggested wording: “BORE-inspired classifier-guided search, using Pareto-rank labels rather than a single-objective quantile threshold.” Do not imply BORE's original expected-improvement derivation directly proves the multi-objective variant. Conversely, using a classifier instead of a Gaussian process does not by itself invalidate the Bayesian-optimization citation.

7. **Qualify composability and the DARTS contrast in Appendix G.** Quantization and other compression axes are potentially complementary, but citing them does not demonstrate plug-and-play compatibility. In particular, combining unequal layer budgets with [MiniCache](https://proceedings.neurips.cc/paper_files/paper/2024/hash/fd0705710bf01b88a60a3d479ea341d9-Abstract-Conference.html)'s cross-layer merging can require additional alignment/integration. Prefer “potentially complementary; joint integration is not evaluated.” For [DARTS](https://openreview.net/pdf?id=S1eYHoC5FX), replace “does not apply here” with “is not directly applicable to our discrete black-box objective without a differentiable relaxation or surrogate.” DARTS itself relies on relaxation, so non-differentiability is not a proof that every gradient-based alternative is impossible.

### Reference-by-reference identity and relevance

Every row below is a real work. Links point to primary publication records, papers or author-hosted originals. “Relevant” means relevant to the role used in MOSAIC, not that every surrounding claim is endorsed.

| Compiled reference | Primary source | Relevance / audit note |
| --- | --- | --- |
| Bai et al., 2024 — LongBench | [ACL](https://aclanthology.org/2024.acl-long.172/) | Direct benchmark reference; appropriate. |
| Cai et al., 2020 — Once-for-All | [ICLR paper](https://openreview.net/references/pdf?id=fP6PibLfO) | Relevant search/train-once deployment analogy; not the same optimization procedure. |
| Cai et al., 2025 — PyramidKV | [COLM](https://openreview.net/pdf?id=ayi7qezU87) | Direct layer-budget prior art; add missing authors and preserve heterogeneity distinction. |
| Dao, 2024 — FlashAttention-2 | [ICLR](https://openreview.net/forum?id=mZn2Xyh9Ec) | Relevant attention implementation/efficiency background. |
| Deb et al., 2002 — NSGA-II | [IEEE](https://ieeexplore.ieee.org/document/996017) | Appropriate for nondominated sorting; does not imply the complete MOSAIC algorithm is NSGA-II. |
| Devoto et al., 2024 — L2Norm | [EMNLP](https://aclanthology.org/2024.emnlp-main.1027/) | Direct eviction baseline; low-key-norm description is appropriate. |
| Elsken et al., 2019 — NAS survey | [JMLR](https://jmlr.org/papers/v20/18-598.html) | Appropriate optimization context; not KV-specific evidence. |
| Feng et al., 2025 — Ada-KV | [NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2025/hash/a40ff56daab9f4808b1e18350c8a11ce-Abstract-Conference.html) | Direct adaptive budget/eviction baseline. |
| Frantar et al., 2023 — GPTQ | [Author preprint](https://arxiv.org/abs/2210.17323) | Relevant offline weight-quantization analogy; narrow static-activation claim needs revision. |
| Fu et al., 2025 — HeadKV | [ICLR](https://openreview.net/pdf?id=FJFVmeXusW) | Relevant head-wise importance/budget allocation prior art. |
| Ge et al., 2024 — FastGen | [ICLR](https://openreview.net/pdf?id=uNrFpDPMyo) | Relevant head-specific cache profiling; separate from H2O's mechanism. |
| Grattafiori et al., 2024 — The Llama 3 Herd of Models | [Author preprint](https://arxiv.org/abs/2407.21783) | Appropriate model-family reference; Grattafiori attribution is real in the updated record. |
| Hansen and Ostermeier, 2001 — CMA-ES | [Author-hosted original](https://www.cmap.polytechnique.fr/~nikolaus.hansen/cmaartic.pdf) | Appropriate optimizer provenance for EvolKV comparison. |
| Hooper et al., 2024 — KVQuant | [NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2024/hash/028fcbcf85435d39a40c4d61b42c99a4-Abstract-Conference.html) | Relevant KV-precision compression; integration with MOSAIC is not tested. |
| Hsieh et al., 2024 — RULER | [COLM paper](https://openreview.net/pdf?id=kIoBbc76Sy) | Direct benchmark reference; final paper supports the listed eight authors. |
| Jiang et al., 2023 — Mistral 7B | [Author preprint](https://arxiv.org/abs/2310.06825) | Appropriate model-family reference. |
| Jones et al., 2026 — QUOKA | [Author preprint](https://arxiv.org/abs/2602.08722) | Real February 2026 preprint; relevant sparse prefill attention, not automatically permanent eviction. |
| Kwon et al., 2023 — PagedAttention | [Author preprint / SOSP record](https://arxiv.org/abs/2309.06180) | Relevant KV memory management and scaling. |
| Li et al., 2024 — SnapKV | [NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2024/hash/28ab418242603e0f7323e54185d19bde-Abstract-Conference.html) | Direct eviction baseline; observation-window description is appropriate. |
| Liu et al., 2024a — MiniCache | [NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2024/hash/fd0705710bf01b88a60a3d479ea341d9-Abstract-Conference.html) | Relevant cross-layer compression; qualify untested composability. |
| Liu et al., 2019 — DARTS | [ICLR](https://openreview.net/pdf?id=S1eYHoC5FX) | Relevant alternative optimization paradigm; avoid categorical impossibility claim. |
| Liu et al., 2023 — Scissorhands | [NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2023/hash/a452a7c6c463e4ae8fbdc614c6e983e6-Abstract-Conference.html) | Relevant importance-persistence eviction; distinguish its rule from H2O. |
| Liu et al., 2024b — KIVI | [ICML](https://proceedings.mlr.press/v235/liu24bz.html) | Relevant KV quantization/complementary storage axis. |
| McKay et al., 1979 — Latin hypercube sampling | [Original DOI](https://doi.org/10.1080/00401706.1979.10489755) | Appropriate sampling reference. Original publisher access restricted; publication identity also confirmed by publisher's later reprint record. |
| Park et al., 2025 — KeyDiff | [NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2025/hash/0907335ecf28faf15be54485dbcbe70e-Abstract-Conference.html) | Real and relevant key-based attention sparsification; preserve scope of access versus eviction. |
| Qin et al., 2025 — CAKE | [ICLR paper](https://openreview.net/pdf/b1d9910c4ac08cd3ef1dfd4459a1f3196028444c.pdf) | Direct adaptive layer/head allocation prior art. |
| Storn and Price, 1997 — Differential Evolution | [Publisher](https://link.springer.com/article/10.1023/A:1008202821328) | Appropriate optimizer reference. |
| Tang et al., 2024 — QUEST | [ICML](https://proceedings.mlr.press/v235/tang24l.html) | Relevant query-aware page access; retains full KV cache rather than reducing its resident size. |
| Tiao et al., 2021 — BORE | [ICML](https://proceedings.mlr.press/v139/tiao21a.html) | Relevant classifier-guided BO; distinguish quantile labels from Pareto-rank extension. |
| Wang et al., 2025 — SqueezeAttention | [ICLR](https://openreview.net/pdf?id=9HK2rHNAhd) | Relevant layer-dependent allocation/compression. Describe importance-based grouping without relying on an unnecessary exact group-count claim. |
| Xiao et al., 2023 — SmoothQuant | [ICML](https://proceedings.mlr.press/v202/xiao23c.html) | Relevant offline calibration analogy; identify static variant if making a narrow activation-scale claim. |
| Xiao et al., 2025 — DuoAttention | [ICLR](https://openreview.net/pdf?id=cFu7ze7xUm) | Relevant offline head identification: retrieval heads retain full cache, streaming heads use bounded cache; not identical continuous layer-budget optimization. |
| Xiao et al., 2024 — StreamingLLM | [Author preprint](https://arxiv.org/abs/2309.17453) | Relevant sink-plus-recent retention; distinguish from accumulated-attention heavy hitters. |
| Yang et al., 2024 — PyramidInfer | [Findings ACL](https://aclanthology.org/2024.findings-acl.195/) | Direct layerwise compression prior art; distinguish attention-based pivotal-context selection from fixed integer budgets. |
| Yu and Chai, 2025 — EvolKV | [Findings EMNLP](https://aclanthology.org/2025.findings-emnlp.88/) | Closest search-based allocation prior art; expansion is real and must remain acknowledged. |
| Zhang et al., 2023 — H2O | [NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2023/hash/6ceefa7b15572587b78ecfcebb2827f8-Abstract-Conference.html) | Direct eviction baseline; supports the introductory 180 GB example. |

### Checks that did not reveal problems

- The introduction's **30B model, batch 128, sequence length 1024, 180 GB KV-cache** example appears in H2O's own introduction. It is a supported source example, not an invented number; do not present it as a measurement from MOSAIC.
- **QUOKA (2026) and KeyDiff (2025) are real.** A recent title or arXiv-only entry is not evidence of hallucination. QUOKA was posted before the current October 2026 submission date.
- Conference years can differ from original arXiv posting years. That alone does not make entries such as PyramidKV, StreamingLLM or GPTQ incorrect. Use a consistent title/author list for the particular version cited. GPTQ also has a conference-record title variant (OPTQ); do not classify the familiar GPTQ preprint title as fabricated.
- The NAS survey, Once-for-All, DARTS, NSGA-II, CMA-ES, DE and LHS references are relevant methodological context. They need not be KV-cache papers, but they should not be used as direct evidence for MOSAIC's measured gains.
- Minor bibliography polish: add article/page information consistently where available (e.g. JMLR 20, article 55 for the NAS survey; EvolKV pages 1673–1689). Protect acronym capitalization in BibTeX if the style lowercases titles. These are presentation issues, not hallucination findings.

**Recommended action:** retain the relevant references, repair PyramidKV's author list, and tighten the claim wording above. Adding citations improves grounding but does not supply missing experimental evidence or by itself change the previous full-paper rating.

## Historical assessment — October 8, 15:08:58 PDF

**Overall remains 3/5 — Findings recommendation.** Soundness 3.5/5, excitement 4/5, reproducibility 3/5, confidence 4/5. The Mistral visual analyses and explanation of when refinement helps improve the presentation. The underlying headline results remain 74/78 Llama and 72/76 Mistral, or 146/154 combined. There is no new held-out evaluation or matched-budget random/LHS experiment. The new abstract introduces useful efficiency-oriented framing, but several claims need more precise qualifications; stronger wording is not additional experimental evidence. These are hypothetical reviewer judgments, not acceptance probabilities or guarantees.

### Improvements credited

- **Mistral analysis is easier to inspect.** New Figure 5 exposes uniform, Winner and NAS-refined curves for Mistral, and Figures 10–12 show its layer allocations across methods. The inspected figures preserve the distinction between rescaled Winners and refined outputs. Dataset heatmaps are now separated by model in Figures 15/16. This gives the second model a fuller analytical treatment, beyond aggregate tables.
- **Section 4.2 now explains the two stages' different roles across models:** Llama's Winner already captures much of the gain, whereas Mistral benefits more from refinement (51/75 Winner wins, 71/76 NAS-refined, 72/76 final). Credit this correction to the search-once-versus-final-workflow interpretation.
- **Missing Mistral summarization scope is explicit:** SnapKV/H2O/AdaKV ran Stage 1 only; Table 2 provides their uniform scores but no final MOSAIC scores. Limitations explicitly defers Stages 2–4. These rows are not new method wins or additions to the 154 evaluated final configurations. L2Norm retains complete summarization results.
- **The abstract's combined count is consistent with the reported subset totals:** 74 + 72 = 146 wins out of 78 + 76 = 154. The aggregate excludes Winner-only cells not covered by Stage 4; Table 1 continues to show the separate 75/87 Llama transfer tally.
- Earlier substantive improvements remain credited: broader Mistral LongBench experiments, completed Llama AdaKV summarization, dataset-level regressions, calibration-fidelity analysis, acknowledgement of EvolKV expansion and explicit stage-specific layer caps.

### New abstract claims: precise scope needed

1. **“Explores a ~10^40 larger search space” is not measured exploration.** The calculation compares a nominal joint fixed-budget proposal domain with one eight-layer EvolKV group-optimization phase. A complete EvolKV search optimizes multiple groups, and both methods share the same global allocation bounds. It does not establish that MOSAIC actually evaluated 10^40 more configurations. Prefer making joint optimization the headline distinction and moving the qualified per-group combinatorial count to the appendix. Do not combine an across-budget Stage 1 narrative with a B128 fixed-budget domain ratio as if these were one measured result.
2. **“18% fewer GPU-hours per budget” must say aggregate incremental Stage 4 cost.** (53.7 - 43.8)/53.7 is approximately 18.4%, but it is the aggregate saving across six matched-comparison cells, excluding Stages 1–2. Savings are not 18% in each cell. End-to-end reported costs remain at least 64.3 versus 53.7 GPU-hours. State “18% lower aggregate refinement cost across six cells, excluding one-time search/selection” if retaining this number. The 600 versus at-most-150 calibration-evaluation comparison supports roughly fourfold fewer evaluations, not equivalence of sample counts or selection protocols.
3. **“A single 9–40 GPU-hour search” is a partial Stage 1 cost range.** Table 13 lists a subset of Stage 1 runs at 9.0–39.7 hours; selecting the deployable anchor also requires Stage 2 (for example, 3.6 hours for Single-Doc SnapKV). Do not imply that this is the total cost of a deployable anchor for every model/method/task. Preserve the incomplete Code Stage 1 cost qualification and identify the scope of this range.
4. **Cache savings are potentially useful, but specify the derivation.** The abstract adds up to fourfold less KV cache and half-cache-or-less in 17 Llama settings. Add a compact accounting table/list identifying the MOSAIC budget, larger uniform reference budget, both scores, cache ratio, selection rule and what counts as one of the 17 settings. Allocated KV token budget is proportional to ideal KV payload under fixed precision/head structure, but this is not measured total GPU memory, latency or throughput. This request does not deny budget-level savings; it asks for an auditable cross-budget result and clear scope. Independent evaluation remains a separate issue.
5. **Restore the abstract's selection caveat.** The former explicit sentence saying configurations are selected/evaluated on full benchmark data is gone, while the new abstract adds several efficiency/comparison claims. Section 3.2 and Limitations retain the disclosure. A concise abstract qualification would prevent readers interpreting 146/154 and the cache-saving pairs as independent-test generalization results.

### Still-open methodological/documentation concerns

- **No independent frozen-allocation evaluation.** Section 3.2 and Limitations explicitly state that selection and scoring share examples. Separately searched Mistral results strengthen breadth, not independent evaluation or cross-model transfer of a frozen allocation.
- **NAS-refined definition remains inconsistent.** Appendix G still includes uniform and Winner in the full-data pool defining NAS-refined, yet the tables show NAS-refined below Winner and sometimes uniform. For example, Mistral SnapKV Single-Doc B128 is Winner 29.50 versus NAS-refined 29.13. Define C and NAS-refined precisely, distinguishing the shortlisted search output from the final better-of-Winner-and-NAS-refined. Explain three-candidate cost accounting and legacy exceptions. This is a manuscript inconsistency, not an audited implementation-error finding.
- **Search-prefix/anchor provenance remains unresolved.** Current cap wording is 180/150; Appendix D still retains historical evaluations at or before 150 in execution order. Show which reported configurations were discovered within those prefixes, whether the carried Stage 1 anchor existed within 180 evaluations, and whether Code B128's previously missing prefix-candidate full-data score was newly evaluated. The current score/cost tables alone do not supply these links.
- **No equal-budget random/LHS or repeated-search control.** The 57 LHS seeds are present and credited. The missing control is the same initial pool plus an equal number of random/LHS rather than guided proposals, evaluated/selected identically. Limitations still says that comparison is absent. Unequal selection data versus EvolKV also remain material to optimizer-attribution claims.
- **Reproducibility metadata is still incomplete, and some disclosure has been removed.** The prior PDF identified floor 16 for Mistral SnapKV/H2O/AdaKV LongBench in Table 7 and marked earlier floor-16 cells in tables/figures. Those details/markers are removed while the scores stay the same; no explicit replacement-run explanation is given. If these were rerun with floor 64, identify the new artifacts/protocol; otherwise restore an exact floor map. Similarly, removing Winner-only daggers does not turn those cells into Stage 4 runs; preserve the distinction somewhere unambiguous. Exact rounding/tie rules, full evaluation settings/seeds and per-experiment hardware remain needed. The universal A100 statement is still not reconciled with earlier H100/A6000 metadata.
- **Earlier writing checks remain:** Stage 4's generic 10% statement needs the Mistral/L2Norm 30% exception; Mistral's maximum loss bound should agree with Table 2's displayed 30.91 versus 30.57; explicitly label the following named losses as Llama. AdaKV Figure 8's natural budgets 396/174/244 still need distinction from Table 5's carried 482/188/464 anchors. The introduction's claim that preceding allocation methods overlook layer differences remains too broad.
- No new measured inference memory/latency/throughput or explicit risks discussion was found. Absence of measured GPU memory does not invalidate ideal cache-budget arithmetic; it limits systems-level claims.

**Bottom line:** a fuller, clearer presentation of the same broad empirical evidence, still a Findings recommendation. The most urgent writing fixes are precise NAS-refined definitions, retained run metadata and careful abstract efficiency scope. The main-conference case still needs independent evaluation and controlled evidence of what the guided search adds.

## Retained historical review — October 8, 12:07:52 PDF

The following assessment refers to the preceding 23-page PDF. Figure numbers, scope disclosures and new abstract claims are superseded by the current assessment above; the underlying coverage counts remain valid.

**Overall: 3/5 — Findings, now a stronger recommendation within that category.** Soundness 3.5/5, excitement 4/5 (up from 3.5), reproducibility 3/5, confidence 4/5. This is a substantive empirical expansion, not merely a wording edit. Broader second-model coverage and completed AdaKV summarization strengthen the contribution. I would not yet move to 3.5/5 (borderline main conference), because the independent-evaluation and controlled-attribution limitations remain and the selection definitions still need reconciliation. These are hypothetical reviewer judgments, not acceptance predictions or guarantees.

### Improvements credited

- **Substantially expanded Mistral LongBench evaluation.** SnapKV, H2O and AdaKV now each cover Code, Single-Doc QA and Multi-Doc QA at four budgets, in addition to the existing L2Norm results and all four RULER methods. Table 7 exposes uniform/Winner/NAS-refined; Table 9 summarizes transfer versus refinement; Table 19 provides dataset scores. Close the old objection that Mistral LongBench evaluates only L2Norm. Summarization remains L2Norm-only on Mistral, and the manuscript now says that explicitly.
- **Current final coverage is 74/78 for Llama and 72/76 for Mistral on the Stage-4-covered sets.** Llama adds three AdaKV summarization cells, all wins; Mistral adds 36 cells, with 32 wins. The change from 40/40 to 72/76 is expanded coverage revealing four small losses, not deterioration on the original 40 cells. Do not continue citing 71/75 and 40/40 as the current totals. Llama's Table 1 denominator excludes Winner-only budgets, which it distinguishes from the 87 Stage 3 cells.
- **Anchor-transfer results are reported separately:** 75/87 Llama and 51/75 Mistral. In the Stage-4-covered Llama subset, Winner wins 67/78, NAS-refined wins 72/78, and NAS-refined matches/beats Winner in 54/78. Mistral Winner wins 40/52 LongBench cells and 11/23 RULER cells; final results win 48/52 and 24/24 respectively. These distinctions are valuable evidence of when refinement is needed.
- **More transparent dataset-level reporting.** Figure 11 now shows both models across all available methods, and Tables 18/19 give the scores. Appendix H.2 reports at least one dataset regression in 23/60 Llama LongBench cells (19 still have positive category means) and 12/52 Mistral cells. The new Mistral heatmap is readable on the inspected page and shows losses rather than hiding them.
- **Some experiment metadata is restored/extended.** Section 4.1 specifies 30% calibration for all Mistral LongBench and L2Norm searches. Table 7 identifies floor 16 for Mistral SnapKV/H2O/AdaKV, 7.5K prompt truncation for H2O and 31.5K for SnapKV/AdaKV. Table 3 discloses legacy 3–4-candidate selection for Llama SnapKV/H2O RULER at B1024 and above. Credit these details rather than claiming all experiment metadata or all candidate exceptions are missing.
- Prior corrections remain closed: EvolKV's allocation expansion is acknowledged; the Stage 1 grid maximum is distinguished from the Stage 3/4 cap; the obsolete 1000-cap statement is removed; initial seeds are distinguished from later guided proposals.

### Highest-priority remaining issues

1. **Independent evaluation remains absent.** Section 3.2 and Limitations still explicitly select and score on the same full benchmark examples. More models/methods strengthen breadth, but do not establish performance of a frozen selected configuration on unseen examples. The Mistral allocations are separately searched, not frozen Llama allocations transferred across models. The existing disclosure is good; it does not replace an independent assessment.
2. **NAS-refined's definition still conflicts with the results.** Appendix G says Stage 4 re-evaluates uniform, Winner and calibration-best search candidates and calls the full-data best NAS-refined. That would guarantee NAS-refined is at least as good as Winner and uniform. Yet Table 7, for example, gives Mistral SnapKV Single-Doc B128 Winner 29.50 versus NAS-refined 29.13, and the text says Winner remains better in 24/78 Llama cells. Define C precisely and distinguish search-shortlist NAS-refined from the final best-of-Winner-and-NAS-refined output. Inclusion in the initial search design is not unconditional inclusion in C. This is a manuscript inconsistency, not a verified implementation error. Table 3's new legacy disclosure is helpful but does not resolve the generic definition or the three-candidate accounting in Appendix D.
3. **Shortened-search provenance remains unestablished.** Current 180/150 cap wording is more consistent, and “at most 200” is compatible with a 180 cap. However, Appendix D still explicitly truncates historical Stage 4 searches at 150 evaluations. Identify original searches versus comparison prefixes/reruns, selected candidate discovery indices, and whether the carried Stage 1 anchors existed within the 180-evaluation prefix. State whether Code B128 55.73 received the previously missing full-data re-evaluation. Cost remains a reported, unaudited at-least 64.3 versus 53.7 GPU-hours end to end, versus 43.8 versus 53.7 incrementally; do not equate incremental savings with total-workflow savings.
4. **The optimizer's incremental advantage is still not isolated.** The 57 LHS seeds are a useful seed-level comparison, but not a same-budget random/LHS search control. Match the initial design and spend the remaining evaluations on random/LHS instead of guidance, using identical calibration and final-selection rules. Limitations still correctly acknowledges the absence of this control. Repeated searches/uncertainty and measured inference memory/latency/throughput remain absent. Fairly distinguish complete-protocol comparison against EvolKV from equal-selection-data evidence about the optimizer.
5. **Complete reproducibility still needs a precise settings table/artifacts.** The new Mistral floor/calibration/truncation details partially address this concern. Exact rounding/tie rules, floor mapping for all cells, evaluation precision/decoding/templates/output lengths, sampling seed, surrogate/DE defaults and accurate per-experiment hardware are still needed. The generic A100-for-all statement remains unreconciled with earlier H100 L2Norm/A6000 AdaKV metadata; identify reruns if they occurred, otherwise retain the actual hardware mapping.

### Writing corrections prompted by the new experiments

- Scope Section 3.2's Stage 4 “10% on both benchmarks” statement to the relevant Llama runs, with the 30% Mistral/L2Norm exceptions stated alongside it. Update Section 4.1's “16 in some earlier RULER runs” and Limitations' corresponding bullet to include the newly documented floor-16 Mistral LongBench runs. Floors differ by protocol; this is not proof of an unfair within-cell comparison, but should be disclosed consistently.
- Section 4.2 says Mistral's four losses are at most 0.33. Table 2's rounded AdaKV Single-Doc B128 scores are 30.91 versus 30.57, a displayed difference of 0.34. Check unrounded scores before choosing a bound; make the prose agree with the reported precision. The subsequent named losses of -0.41/-0.04/-0.74/-0.20 refer to Llama: label that explicitly after the Mistral sentence.
- Keep the central claim about **the full workflow** separate from universal anchor transfer. Mistral Stage 3 is 51/75, not 72/76; AdaKV Code rescaling loses all four budgets despite refinement winning all four. Discuss that informative limitation rather than implying every method benefits from search-once reuse alone.
- The 10^40 comparison still calls an eight-layer group-optimization phase “one EvolKV search.” Use the precise phase/proposal-domain unit; nominal domain size is not actual explored coverage or proof that joint optimization is necessary. The introduction's claim that preceding layer-allocation methods overlook layer differences is also too broad given the cited methods' purpose.
- Figure 7's AdaKV plotted natural budgets 396/174/244 still differ from Table 5's carried calibration anchors 482/188/464. Distinguish full-data plotted winners from calibration-selected carried winners. Explain whether Limitations' 0.17–0.82 deficit applies only to the previously analyzed fronts or includes the new summarization/Mistral fronts.
- No new explicit ethical/societal/environmental risks discussion was found. Match the responsible-NLP checklist to the actual compiled content.

**Bottom line:** this revision meaningfully strengthens the breadth and transparency of the empirical contribution, and I raise excitement to 4/5. Overall remains a stronger 3/5 Findings recommendation. Clear selection definitions and search provenance are urgent writing/documentation fixes; held-out evaluation and a matched-budget control remain the strongest routes to a main-conference recommendation.

## Retained historical review — October 7, 17:24:12 PDF

The following assessment refers to the preceding 21-page PDF. Its coverage counts and missing-second-model-coverage concerns are superseded by the October 8 assessment above.

**Overall remains 3/5 — Findings.** Soundness 3.5/5, excitement 3.5/5, reproducibility 3/5, confidence 4/5. The latest edit removes the conflicting 1000-evaluation cap from Section 3.2. Credit that correction; it is no longer a current textual contradiction. The initial-design clarification and stage-specific cap correction remain credited. The empirical evidence is unchanged, and search-prefix provenance, selection definitions and missing reproducibility metadata remain material. These are hypothetical reviewer judgments, not acceptance predictions.

### What changed and is credited

- **17:24 correction: obsolete 1000-cap statement removed.** Section 3.2 now says 180/150 evaluations, matching Appendix G's stage-specific limits. Prefer spelling out Stage 1 = 180 and Stage 4 = 150, since this sentence is inside the Stage 4 paragraph. Section 3.1's “at most 200” for Stage 1 is a looser upper bound, not logically incompatible with 180; standardizing the wording is a clarity improvement, not a new soundness objection. The separate question of which historical configurations were available within these prefixes remains open.
- **17:20 addition: Stage 4 initial design is explicit.** The 64 configurations comprise uniform + five heuristic shapes + the Winner + 57 LHS points; subsequent evaluations are guided proposals. Credit this clear distinction between seeds and later optimization. The LHS pool is a useful seed-level random-allocation comparison, but not an equal-budget random-search control: a search capped at 150 has up to 86 additional guided evaluations beyond its 64 initial points. To isolate guidance, compare against the same initial design followed by the same number of additional random/LHS evaluations, with matched selection rules and data. Limitations correctly still says no equal-cost random-search comparison is provided. Do not claim random allocations are entirely absent; the missing evidence is the matched-budget control.
- **Latest correction: stage-specific cap resolved.** Appendix G now explicitly distinguishes Stage 1's grid maximum (1024 for most LongBench runs, 4096 for RULER) from the 4096 per-layer cap used in continuous Stage 3/4 decoding, with a floor of 64 or 16. This removes the contradictory interpretation at B1024. The earlier cap ambiguity is no longer an outstanding concern.
- Algorithm 1 gives a clear overview of exploration, Pareto selection, anchor rescaling, optional refinement, and the surrogate-guided search loop.
- It makes **full-data selection explicit** at lines 4, 10 and 11: choose the anchor using D_full, choose NAS-refined among calibration-shortlisted candidates using D_full, and compare Winner versus NAS-refined on D_full. This resolves uncertainty about what the manuscript claims, but does not establish independent evaluation. If it matches implementation, do not continue describing the final choice as calibration-only.
- The prior calibration/transfer/second-model analyses remain credited. Reported final coverage remains 71/75 Llama and 40/40 Mistral; Stage 3 transfer remains 74/84 and 27/39 respectively. No new independent test or controlled experiment appears in the diff.

### Corrections needed in the current appendix

1. **Stage-specific cap — resolved in the 17:05:53 revision.** Do not retain this as an active criticism. A precise run-settings table would still aid reproducibility, but the distinction between the Stage 1 grid maximum and the Stage 3/4 cap is now clear.
2. **Document original searches separately from comparison prefixes.** The 1000-cap textual contradiction is now resolved. Appendix G and Section 3.2 state 180/150, while Appendix D still explicitly keeps each run's first 150 evaluations in execution order. Establish whether the shorter limits describe new reruns, historical original runs, or retrospective prefixes, and identify which results each protocol produced. Updating the cap sentence does not by itself establish that the unchanged main-table Winner/NAS-refined configurations were discovered within those shorter limits. Keep candidate-discovery provenance, especially for the Stage 1 anchor and Code B128 prefix score. Standardize Section 3.1's looser 200 upper bound for clarity, without treating 180 versus “at most 200” as a logical contradiction.
3. **Restore evaluation and hardware metadata.** The precision, decoding, prompts/chat template, truncation, output lengths, scoring details, calibration sampling seed, and prior per-method hardware mapping are removed. The appendix now says experiments ran on A100 GPUs, whereas the earlier manuscript separately documented H100 L2Norm and A6000 AdaKV runs. If all results were genuinely rerun on A100, explicitly identify that and the replacement artifacts; otherwise restrict A100 to the matched comparison and preserve the real hardware per experiment. Restoring accurate metadata is preferable to simplifying it into an unsupported universal statement.
4. **Define the candidate shortlist C and distinguish NAS-refined from the final output.** Algorithm 1 line 9 and the prose say calibration-best “candidates” but no longer specify best heuristic/LHS/guided groups. Table 11 and Appendix D still account for three candidates. State exactly how C is formed, how many candidates it contains, whether uniform/Winner are included in NAS-refined or handled separately, and retain legacy exceptions. In particular, Appendix G's Candidate provenance paragraph says NAS-refined is the best on full data among uniform, Winner and shortlisted candidates. That would imply NAS-refined never scores below Winner or uniform, whereas Section 3.2 says NAS-refined matches/beats Winner in only 51/75 cells and reports the final output as a separate best-of-Winner-and-NAS-refined. Reconcile those definitions; this is a manuscript inconsistency, not a verified implementation error. The new initialization paragraph does not resolve it, because inclusion in the initial design is different from unconditional inclusion in the final full-data shortlist. The AdaKV calibration-selected Stage 2 exception remains in Limitations but disappears from the generic Algorithm 1; point readers to explicit exceptions.
5. **Preserve complete implementation details in accessible supplementary material.** The shortened decoder omits largest-remainder/tie rules; floors are just “64/16” without the exact cell mapping; heuristic shapes lose their formulas. Lost-archive/timing qualifications are also removed. Do not imply removed records have become available. A readable pseudocode overview can coexist with a precise settings table and a fully specified floor-aware decoder.

### Unchanged scientific questions

Independent evaluation remains explicitly absent; selection-data asymmetry versus EvolKV is not highlighted next to Section 6; the nominal 10^40 proposal-domain comparison still needs per-group rather than full-run terminology; equal-cost random/LHS and repeated-search evidence remain absent. The new reported costs from the previous revision remain approximately at least 64.3 versus 53.7 GPU-hours end to end, with 43.8 versus 53.7 for incremental refinement, subject to provenance. The earlier 75.3 figure is historical, not the current reported total. Figure 7's AdaKV full-data-winner budgets still require distinction from the carried calibration anchors. No new measured inference-memory/latency/throughput or explicit risks discussion is present.

**Bottom line:** retain Algorithm 1, but restore the precise experiment metadata alongside it. The paper is still interesting enough for a Findings recommendation in my judgment; this edit improves exposition, not the missing independent/controlled evidence needed for a stronger main-conference case.

## Retained historical review — October 7, 14:44:57 PDF

The following review refers to the earlier 14:44:57 version and is superseded where the current assessment above identifies changed appendix text. Its credit for the empirical coverage and figures remains valid.

### Ratings and recommendation

**Overall: 3/5 — Findings, unchanged.** Soundness 3.5/5, excitement 3.5/5, reproducibility 3/5, reviewer confidence 4/5. The revised visual analyses are clearer, the broader model/method evidence remains useful, and some earlier reporting concerns are answered. The underlying main results and independent-evaluation limitation are unchanged. The new shortened-run cost accounting needs stronger provenance before it can support the revised compute-efficiency claim. These are hypothetical reviewer judgments, not acceptance probabilities.

### Improvements credited

- **Figure 5 is substantially better:** full-width four-panel layout, distinct LongBench circles/RULER triangles, explicit Llama scope, per-cell points and medians, and the warning that zero median regret does not imply correct selection in every cell. The compact Table 9 retains means and correct-pick counts. The earlier readability/scope/marker recommendations are addressed.
- **Stage 1/front analysis is added:** the paper reports high front-order agreement but correctly explains the confounding budget trend. In 13/15 analysed fronts, calibration/full-data Kendall correlation equals budget/full-data correlation; full data prefers a cheaper allocation than the calibration-top one in 4/15 fronts, by up to 0.73 points. This is a useful distinction between ranking the whole front and identifying its top configuration. AdaKV's omission from the bottom panels is explicit; explain the rationale as well.
- **AdaKV calibration-anchor exception is clearer:** Limitations now quantifies the calibration-selected anchors' deficit of 0.17–0.82 versus the full-data best on their fronts. Credit this disclosure. The plot/table identity issue is narrower now: Figure 7(a)'s 396/174/244 budgets still differ from the 482/188/464 carried anchors in Table 5 and need explicit labels identifying which selection rule each uses.
- **Floor reporting improves:** Table 13 now refers specifically to MOSAIC's final configuration and drops the earlier uniform-as-best rows. Appendix E removes the unsupported floor-independent conclusion and focuses on low-budget floor binding plus the controlled floor comparison. Close those specific wording/scope objections. H2O Single-Doc B128's floor count remains 9; with no vector audit, this number is not established as wrong merely because the former label was wrong. Confirm it was calculated from the selected Winner vector.
- **Broader descriptive analysis:** Figure 6 makes cross-task/cross-method transfer easy to inspect; Figure 8 adds L2Norm allocation patterns; Figures 9–11 expose subtask/dataset improvements and regressions. Appendix H reports dataset-level regressions in 22/57 Llama LongBench cells, including 18 positive category means, and 0/16 Mistral L2Norm cells. This adds transparency rather than hiding weaker subsets.
- **Reported coverage remains:** final 71/75 Llama and 40/40 Mistral wins over uniform; Stage 3 transfer 74/84 Llama and 27/39 Mistral. NAS-refined beats uniform in 69/75 Llama cells and matches/beats Winner in 51/75. These are the current denominators, not the older 72/82 transfer tally.
- **Cost comparison now explicitly uses prefixes:** Appendix D states that Stage 4 keeps evaluations at or before 150 in execution order and adds full-data re-evaluation of three candidates. This clarifies that the shortened comparison is not the cost of all original runs. The new table reports 43.8 versus 53.7 GPU-hours incrementally, still with more total cost after upstream stages.

### Highest-priority remaining manuscript checks

1. **Provenance for the new prefix scores/costs is essential.** Table 11 replaces the prior capped-compute/lower-bound presentation with exact scores, including Code B128 55.73, at no more than 150 evaluations. The earlier PDF explicitly said the within-prefix guided candidate had not been re-evaluated, so its capped score was a lower bound. If that evaluation has now been performed, say so and supply the selected candidate index/origin; otherwise retain the lower-bound qualification. Likewise, Table 12 reports a 180-evaluation Stage 1 cost (Single-Doc SnapKV 9.0 GPU-hours, formerly 16.5 for 331 evaluations). Establish that the actual carried Winner and its Stage 2 shortlist were available within that prefix; scaling the original time down to 180 rows does not by itself establish the same anchor was produced. These are provenance checks, not claims that no new evaluation occurred.
2. **Distinguish short comparison prefixes from the searches producing the main results.** Section 3.1 still says searches evaluate at most 200 configurations in Stage 1 and 150 in Stage 4, while Section 3.2 and Appendix G retain a 1000 cap, saturation-watchdog runs and hand stopping. Appendix D now documents the 150-row comparison prefix, but that is not a universal original-run limit. Put this scope qualification next to the main-text statement; preserve original run lengths in artifacts or a supplementary table. The same applies to 180-evaluation Stage 1 costs. Do not silently replace historical run metadata with a shorter reference protocol.
3. **Full-data selection remains the documented protocol.** Section 3.2, Appendix B and Appendix G explicitly select shortlisted configurations on full data. Appendix G still chooses the best of calibration-top heuristic, LHS and guided candidates using full-data scores, then the final method compares Winner versus NAS-refined on those scores. This is not the single calibration-selected, frozen-output procedure described in conversation. If the implementation differs, reconcile the manuscript and cost accounting; otherwise accurately retain the selection-dependence limitation. Stage 2 has separate AdaKV/RULER exceptions that should appear alongside the general rule.
4. **Restore the comparison's unequal-selection-data qualification.** EvolKV uses 30 calibration samples and MOSAIC selects shortlisted outputs on full data; that remains visible only by piecing together separate sections. State near Section 6/Table 4 that these are complete-protocol comparisons and not controlled proof of joint search or optimizer superiority. The Single-Doc Winner-versus-direct gains of only +0.01–0.06 are numerical observations, not demonstrated robust improvements.
5. **Use precise search-space units and modest claims.** The old 10^53 global-domain argument remains closed; Appendix G acknowledges a common global allocation space. The 10^40 count is conditional proposal-domain combinatorics. Sections 3/6 still call one eight-layer phase “one EvolKV search,” although a complete run processes all four groups. Say one group-optimization phase throughout; do not imply actual coverage of all nominal vectors or that greater cardinality proves superior search. Remove the statement that layers “must” be chosen jointly unless necessity is demonstrated.
6. **Local consistency/clarity checks:** label Figure 7's full-data-best AdaKV anchors separately from the carried calibration-best ones; clarify whether Figure 5's Stage 1 “15 fronts” includes all rank-1 candidates or shortlists (RULER H2O previously re-evaluated only four), and explain why AdaKV is omitted; carry the H2O Single-Doc B128 candidate-pool exception into Figure 5/Table 9 or the accompanying text; qualify “Across tasks, shapes do not transfer” to the tested SnapKV Code/Single-Doc settings; scope the introduction's +1.3–2.1 Code margin to B256–B1024. The compact decoder drops some previously specified implementation details; retain a complete floor-aware decoder, shape formulas, rounding/tie rule and software versions in accessible reproducibility material. A promised future code release is helpful but not an artifact available for review. The evaluation-settings paragraph still names Llama rather than explicitly giving Mistral's settings.

### Remaining experimental limits and main-conference case

- **Independent frozen-allocation evaluation is still absent.** Limitations explicitly says no held-out examples are evaluated. The new descriptive analyses and second model do not remove selection optimism; they strengthen only the appropriately scoped empirical contribution.
- **No equal-data/equal-end-to-end-compute attribution or random/LHS control is added.** A seed/heuristic can legitimately win, but this does not establish what additional guided optimization adds. Repeated-search/uncertainty evidence would help interpret small gains.
- **Final-method success and anchor-transfer success remain distinct:** Mistral final results win 40/40, but Stage 3 wins 27/39 and most SnapKV/AdaKV RULER rescalings lose. Explain where refinement is needed rather than implying universal search-once reuse.
- **Cost numbers changed; do not keep the obsolete 75.3 lower bound as the current reported total.** The new Appendix D gives at least 43.1 versus 38.3 GPU-hours for Code and 21.2 versus 15.4 for Single-Doc including upstream stages: approximately at least 64.3 versus 53.7 combined, subject to the prefix/anchor provenance checks above. These new totals are manuscript reports, not independently verified timings. End-to-end search still costs more; incremental refinement savings are not total-workflow savings.
- **Practical efficiency remains unmeasured:** no new measured inference memory/latency/throughput or amortization analysis was found. No explicit ethical/societal/environmental risk discussion was found either; match the checklist response to the compiled paper.

**Bottom line:** a clearer, more informative empirical paper, still a Findings recommendation in my judgment. Credit the presentation and scope corrections, but prioritize prefix/anchor provenance and a consistent selection protocol before using the updated cost comparison as stronger evidence. Held-out evaluation and a focused controlled advantage remain the clearest ways to strengthen the main-conference case.

## Retained historical review — October 6, 10:55:50 PDF

The following assessment refers to the earlier 23-page PDF. Its table numbers and cost totals are superseded by the October 7 review; explicitly closed issues remain closed.

### Recommendation and scores

**Overall: 3/5 — Findings, unchanged.** Soundness 3.5/5, excitement 3.5/5, reproducibility 3/5, confidence 4/5. The 10:55:50 revision substantially addresses the specific global-domain and exact-budget-count objections: it explicitly recognizes a shared allocation space and uses an unconstrained bounded eight-layer count. Credit that correction; the old 10^53 claim is no longer a current objection. The remaining 10^40 comparison is a conditional per-block proposal-domain comparison, not demonstrated global search coverage or effectiveness. The unsupported 200/150 evaluation-limit statement and documented selection-procedure discrepancy remain. No new held-out or controlled-attribution experiment is reported. These are hypothetical reviewer judgments, not acceptance probabilities.

### Improvements credited

- **Search-space correction (10:55:50 follow-up):** Appendix I now explicitly says both methods' allocations lie in the same [64,4096]^32 space. It replaces four summed exact-budget slices with the count of every bounded eight-layer vector, 4033^8, approximately 7 x 10^28, explicitly ignoring CacheScore's penalty. The approximate 10^40 ratio to the joint exact-budget B128 count is arithmetically consistent under those bounds. This resolves the specific earlier misrepresentation of global representability and the imposed exact-equality count for EvolKV. The remaining qualification is that one eight-layer group-optimization phase is not one complete EvolKV run; use that precise unit throughout.
- Section 6 now explicitly says that both methods can rescale one allocation or search at each budget. It correctly emphasizes where the initial allocation comes from: fixed-target-budget blockwise CMA-ES versus joint budget–score exploration with an anchor. This closes the direct-versus-expanded framing objection; merely having those two options is not claimed as the distinction.
- The new search-once-versus-direct result block is supported by Table 4: MOSAIC Winner is numerically ahead in all six cells where direct EvolKV was run. Code margins are +0.94 to +1.32; Single-Doc margins are only +0.01 to +0.06. This is a valid descriptive comparison, not evidence of robust superiority or isolated optimizer improvement.
- Tables 5–8 now separately expose uniform, Winner and NAS-refined results for both models and benchmarks. Tables 24–26 add accessible RULER subtask and LongBench dataset detail, including Mistral. The previous unavailable per-cell Mistral anchor/refinement breakdown is substantially answered at the manuscript level.
- Search-once coverage is now 74/84 for Llama: SnapKV Summarization B1024 is included and H2O RULER B2048 has a Winner score of 88.31. Final coverage remains 71/75 Llama and 40/40 Mistral. Winner beats uniform in 66/75 Stage-4-covered cells, NAS-refined in 69/75, and NAS-refined matches/beats Winner in 51/75. Different denominators are explained by the evaluated sets.
- **Figure 3's specific H2O Single-Doc B128 marker is corrected:** visually inspected on page 6, it now identifies Winner rather than NAS-refined, consistent with 29.72 versus 28.32. Close that particular figure-label objection. Table 20 still identifies NAS-refined, so the related floor-analysis issue is not fully resolved. No raw-vector audit was performed.
- The explicit independent-evaluation limitation, optional Stage 4, detailed decoder, and end-to-end upstream-cost caveats remain credited. Appendix D explicitly retains at least 75.3 versus 53.7 GPU-hours including upstream work.

### Highest-priority corrections before submission

1. **New evaluation-limit statement contradicts the paper's runs.** Section 3.1 says a search evaluates at most 200 configurations in Stage 1 and 150 in Stage 4. Table 17 reports Stage 1 runs of 331 and 444 evaluations; Table 18 includes 450. Table 15 reports Stage 4 runs of 542 and 1000, and Appendix I gives a 1000-evaluation cap with run-specific exceptions. State actual historical run lengths and caps consistently. If 200/150 are a proposed future/default protocol, label them as such and do not imply they produced the reported results without a valid prefix evaluation.
2. **Prior global search-space objection substantially resolved; qualify the remaining per-block comparison.** The previous 10^53 claim and sum-of-four-exact-budget-slices argument are gone. Counting all bounded eight-layer vectors instead, and explicitly acknowledging a shared global allocation space, addresses those specific objections. Under the stated common bounds the remaining approximate 10^40 ratio is a legitimate combinatorial comparison of a joint exact-budget proposal domain against one fixed-other-layers block domain. However, the introduction/Section 6/Table 23 still call that block phase “one EvolKV search”; a complete EvolKV run optimizes all four groups successively. Say **one group-optimization phase** or **one proposal's degrees of freedom**, not one complete run. These are nominal possible allocations, not the number actually explored; a larger domain alone proves neither better search nor a need for joint optimization. Section 3.1 still concludes that all layers “must” be chosen jointly without evidence of necessity. This is a narrower wording/interpretation qualification, not the earlier global-domain objection repeated. Source: [EvolKV Section 3.2 and Algorithm 1](https://aclanthology.org/2025.findings-emnlp.88.pdf).
3. **The compiled PDF still describes full-data selection in Stage 4, despite the subsequent conversational explanation of one calibration-selected output.** Section 3.2 says the best candidates are re-evaluated and the best is reported as NAS-refined; Appendix I lines 881–886 explicitly re-evaluate the calibration-best heuristic, LHS and guided candidate, then select the best of those three on full data. Appendix D still budgets full-data evaluation of three candidates. The final Winner-versus-NAS-refined comparison also uses full-data scores. This review must follow that documented procedure until clarified. If the actual implementation freezes exactly one calibration-selected output before full-data evaluation, align all relevant text/tables/cost accounting with the implementation; do not merely relabel a three-way full-data comparison as evaluation. Stage 2 anchor selection remains a separate issue.
4. **Restore the unequal-selection-data caveat near the EvolKV comparison.** The former Section 6 and summary-table caveats about EvolKV selecting on 30 samples versus MOSAIC's full-data selection have been removed. The methods/Limitations still describe full-data selection, and Appendix D retains EvolKV's 30-sample protocol, so that asymmetry remains material. Reinsert a concise qualification that these are complete-protocol comparisons and may partly reflect different selection data. Moving it out of sight does not create a controlled optimizer comparison. The +0.01–0.06 Single-Doc margins should be described numerically, not as robust superiority without uncertainty evidence.
5. **Remaining allocation identities need reconciliation.** Table 20 still calls H2O Single-Doc B128 NAS-refined with 9/32 floor layers, despite Table 5 selecting Winner 29.72. Figure 8(a) still gives AdaKV natural budgets 396/174/244 for Code/Multi-Doc/Single-Doc, while Table 5 gives anchors 482/188/464. Limitations says AdaKV LongBench winners were calibration-selected, unlike the general full-data Stage 2 description. Distinguish a plotted full-data winner from a carried calibration winner if that explains the discrepancy, and verify the actual vectors and any affected frequency/floor calculations. Table 20's inclusion of uniform as best also needs its pool distinguished from MOSAIC's defined better-of-Winner-and-NAS-refined final output.

### Remaining interpretation and reproducibility questions

- **No held-out assessment:** both Section 3.2 and Limitations still explicitly state that selection and reported evaluation share examples. Nothing in this revision establishes prospective performance of a frozen allocation on unseen examples.
- **Search-once success is mixed on Mistral:** Tables 7/8 now make clear that L2Norm transfer wins in all 22 of its cells, but SnapKV, H2O and AdaKV RULER transfer wins in only 1/6, 3/6 and 1/5. The overall 40/40 final result mainly strengthens the complete workflow/refinement case, not universal anchor transfer. Table 1's 27/39 transfer tally is informative and should be discussed.
- **No equal-cost random/LHS control or repeated-search uncertainty:** Table 22's initial-versus-full calibration-pick analysis is useful but does not isolate additional guided search. A seed/heuristic winning is a legitimate search output and is not itself a defect.
- **No new measured inference efficiency:** cache-budget allocation and improved task scores do not by themselves measure memory/latency/throughput benefits. Total offline search remains more costly in the documented comparison; the incremental Stage 4 cap excludes upstream work.
- **Minor writing/specification issues persist:** the introduction's +1.3–2.1 Code expansion margin needs its B256–B1024 qualifier (B128 is +0.94); scope Table 23's benchmark row to this reproduction, since published EvolKV also tests GSM8K/NIAH/RULER; Appendix D's matched-cost pointer should reference Table 16, not Table 15; preserve the at-least sign for Code B128's delta; parameterize the decoder by legacy floors; distinguish floor feasibility from search-path independence; clarify Figure 5's not-used-for-main-results scope; qualify correlations among allocations even after removing rescaled Winners; state Mistral evaluation settings explicitly. No explicit ethical/societal/environmental risk discussion was found.
- **Dataset-regression concern is not renewed as a missing-results objection:** Table 26 now provides the underlying per-dataset scores. The earlier corrected regression-summary row was not an implementation-error finding; the reorganized appendix should be interpreted using current table numbers.

**Bottom line:** the specific global-domain search-space concern is substantially addressed, and that correction is credited. Overall stays 3/5 because the independent-evaluation, attribution, evaluation-limit and allocation/selection-provenance questions remain. Qualify the 10^40 comparison as per-block proposal freedom, fix the 200/150 statement, and reconcile the documented selection procedure with the actual one. The evidence-backed distinction remains joint budget-range exploration and seeded refinement.

## Retained historical review — October 6, 06:51:55 PDF

The following assessment refers to the earlier 24-page PDF. Its table numbers, transfer counts and open figure-marker objection are superseded by the 10:48:11 assessment above; its second-model evidence remains credited.

### Recommendation and scores

**Overall: 3/5 — Findings, unchanged but more strongly supported.** The substantial second-model evaluation improves the empirical contribution. It does not establish held-out generalization, isolate the search procedure's benefit, or resolve remaining allocation-analysis inconsistencies. I would not automatically raise the recommendation merely because the experiment count increased, but the Mistral results are meaningful new evidence rather than just wording changes.

| Dimension | Current score | Change / reason |
|---|---|---|
| Overall | **3/5 — Findings** | Stronger breadth and presentation; still not a main-conference recommendation in my assessment. |
| Soundness | **3.5/5** | Claims are qualified and the second-model evidence is useful; selection dependence and figure/table provenance still limit interpretation. |
| Excitement | **3.5/5** | Up from 3: the expanded Mistral coverage and more accessible allocation analysis make the empirical study more interesting. |
| Reproducibility | **3/5** | Considerable protocol detail, but missing archives/timings, unseeded stochastic components, subjective/uneven stopping, and conflicting allocation identities remain. |
| Reviewer confidence | **4/5** | Manuscript and important tables checked; no implementation or raw-result audit. |

These are hypothetical reviewer judgments, not acceptance probabilities. The [ARR review form](https://github.com/acl-org/aclrollingreview/blob/main/reviewform.md) calls 3 Findings and 3.5 Borderline Conference; excitement is distinct from overall recommendation.

### Changes credited

- **Second model added:** Mistral-7B-Instruct-v0.2 is evaluated with all four eviction methods on RULER and with L2Norm across the four LongBench categories. Tables 2 and 3 report 16 LongBench and 24 RULER final-score comparisons, all above their corresponding uniform baselines. This meaningfully answers the previous single-model scope concern; do not continue describing the current paper as single-model. These are separately searched allocations, not evidence that a Llama allocation transfers to Mistral without search.
- **Llama coverage:** Table 1 reports final results above uniform in 71/75 cells. Stage 3 beats uniform in 72/82; I counted 82 rows and 72 positive deltas in Table 13. NAS-refined beats uniform in 69/75 and matches/beats Winner in 50/74 comparable cells. Different denominators reflect different evaluated sets and are not themselves an inconsistency.
- **More readable organization:** the pipeline diagram, main-text uniform-versus-final tables, budget-transfer summary, and origin-marked heatmaps clarify the workflow and its outputs. Figure 8 adds the AdaKV allocation analysis.
- **Search dynamics:** Appendix G/Table 25 explicitly compares calibration-selected configurations after the initial 64 evaluations and after the complete search. On those eight SnapKV LongBench cells, the reported mean gain is +0.72 initially versus +0.47 after the full search. The paper correctly distinguishes these calibration-only picks from the final full-data shortlist. This is useful descriptive evidence, not an equal-compute random/LHS control.
- **Candid limitations:** no held-out evaluation, additional upstream cost, unequal settings, and no equal-cost random-search comparison are explicit. The previous missing-uncertainty phrase “within noise” is removed from Section 6. The rescaling/rounding documentation, Evo expansion comparison, complete-workflow interpretation, and previously corrected dataset-regression table remain credited.
- **Table 7 (formerly Table 8) regression correction remains closed:** it reports 20/54 cells with at least one dataset regression, including 16 positive category means. Do not revive the removed H2O Single-Doc B128 regression-row objection. Table 8's calibration-only exclusion of that cell's Stage 3 Winner remains explicitly justified.

### Highest-priority writing / consistency fixes

1. **Selected-allocation identity still disagrees across results and analysis.** Table 5 gives H2O Single-Doc B128 Winner 29.72 versus NAS-refined 28.32, so the final configuration is Winner. Figure 3(b), visually inspected on PDF page 6, still marks this row with the hollow NAS-refined marker; Table 20 still lists NAS-refined with 9/32 layers at the floor. Use the actual selected vector and recompute affected frequencies, or explicitly scope the analysis to a different pool. This is a manuscript/provenance mismatch, not a confirmed implementation error. Table 20 also calls uniform best for some losing cells although the defined final method excludes uniform; distinguish best-of-all-candidates from MOSAIC's better-of-Winner-and-NAS-refined output.
2. **AdaKV anchor identities disagree.** Figure 8(a) labels its Stage 2 natural budgets as Code 396, Multi-Doc 174, and Single-Doc 244; Table 13 identifies the rescaled anchors as 482, 188, and 464 respectively. Limitations says AdaKV LongBench anchors were selected on calibration, whereas Section 3.2 and Appendix J's general Stage 2 description say full-data selection. If Figure 8 plots full-data winners but the transfer experiments use calibration winners, state this explicitly and do not call both the same carried Stage 2 winner. Reconcile the plots, rescaled vectors, and protocol before relying on their joint interpretation.
3. **Separate final-method success from search-once transfer on Mistral.** Table 1 reports final gains in 40/40 cells, but Stage 3 wins only 27/39: SnapKV RULER 1/6, H2O 3/6, AdaKV 1/5, versus L2Norm 6/6. These results strengthen the complete workflow and refinement case, not a universal search-once transfer claim. Bring this contrast into the main discussion/abstract qualification rather than leaving readers to infer it from Table 1.
4. **Scope the EvolKV descriptions precisely.** Section 1's Code +1.3–2.1 applies to B256–B1024, not every budget (B128 Winner margin is +0.94). “Matches it on Single-Doc QA” needs the B256 loss of -0.92 already reported in Section 6. The claim in the first introduction paragraph that previous allocation methods overlook layer-specific importance is inappropriate for EvolKV, which explicitly motivates its method by layer heterogeneity. In Table 26, label benchmark/data/model rows as this reproduction's settings, not published EvolKV's complete coverage; its published evaluation includes LongBench, GSM8K, NIAH and RULER. See [published EvolKV](https://aclanthology.org/2025.findings-emnlp.88.pdf).
5. **Do not overstate independence in the allocation-frequency analysis.** Removing 16 explicitly rescaled Winners is a useful sensitivity analysis. The remaining Stage 4 allocations can still be correlated through their shared anchor, initial design, and search history. Describe the frequencies as descriptive patterns, not independent evidence of universally important layers or a causal explanation. The original headline allocation-origin objection is not being renewed merely because seeds can win.
6. **Small remaining specification/reporting fixes:** Appendix D calls Table 15 the matched-cost comparison although the capped-prefix comparison is Table 16. Preserve the lower-bound sign for Code B128's delta (at least +0.81) in Table 16/Section 6. Appendix J's default decoder still writes [64,4096] and the feasibility condition with floor 64 despite floor-16 exceptions: parameterize it by the run's floor. “Floor-independent” at B1536/B2048 does not follow just from having no layer exactly at 16; show feasibility at 64 and separate that from search-path independence. Figure 5's “not used for the main results” needs clarification since the main tables include floor-16 SnapKV B1024 configurations. For Mistral, explicitly state model precision, tokenizer/chat-template/truncation settings and shortlisting exceptions; the evaluation-settings paragraph currently names Llama only, and some AdaKV searches ended after just 3–26 evaluations.
7. **No explicit ethical/societal/environmental risk discussion was found in this compiled PDF.** GPU-hour reporting is not a discussion of environmental risk. Keep the Responsible NLP checklist response accurate, or add and compile a short risks discussion if answering Yes. This alone is not the basis for the overall score.

### Remaining experimental questions

- **Independent assessment remains absent:** Section 3.2 and Limitations explicitly say selected and reported scores use the same examples and no held-out examples are evaluated. Adding another model under the same selection protocol broadens evidence but does not remove selection optimism. A prospective frozen-allocation test is the highest-value next addition for deployment/generalization claims.
- **Comparative attribution:** the EvolKV reproduction uses 30 selection examples while MOSAIC uses the full evaluation data, and joint versus blockwise search is not isolated. A controlled comparison with comparable data access and end-to-end compute would substantiate the core workflow advantage. Published EvolKV already supports cross-budget expansion; that feature alone is not new.
- **Optimization contribution / repeatability:** Table 25 is useful but neither an equal-budget random/LHS baseline nor repeated-search uncertainty. The final search may legitimately return a seed or heuristic; the remaining question is what further guided evaluations add relative to alternatives at the same cost. Small margins need uncertainty evidence before being interpreted as robust advantages.
- **Practical efficiency:** no new measured inference-memory/latency/throughput results were found. At the same average budget, better task scores are quality gains, not measured speed gains. Single-Doc one-time search still costs 20.1 versus 5.2 GPU-hours; the six-cell capped refinement comparison still costs at least 75.3 versus 53.7 including upstream work. Do not claim total search-cost superiority. Practical measurements and amortization would particularly help an MLSys case, but not every systems experiment is mandatory for an ARR empirical study.

**Bottom line:** this revision is a stronger and broader Findings paper. The second-model evidence raises excitement, while independent evaluation and a convincing controlled/practical advantage remain the clearest routes toward a main-conference recommendation. First reconcile the selected vectors and anchor identities; those fixes improve trust in the current evidence without requiring an entirely new experiment suite.

## Retained historical review — October 3, 11:39:50 PDF

The following text refers to the earlier 22-page PDF. Its counts, figure/table numbers and ratings are superseded by the October 6 assessment above. Closed concerns remain closed.

### October 3 assessment

### Changes credited

- Final MOSAIC coverage grows from 63/67 to **70/74** wins over uniform. Table 6 adds SnapKV Summarization B128, H2O Single-Doc B128, all four H2O Summarization budgets, and a floor-64 SnapKV RULER B128 Stage 4 result.
- SnapKV RULER B128 now reports **58.37 versus 51.56 uniform**, replacing the earlier floor-16 Winner score of 61.08. This is a useful, more comparable floor-64 search result; the lower score is not itself a defect.
- RULER B128 for SnapKV and H2O has no floor-matched rescaled Winner in Tables 4/6. The floor-16 B128 rescalings are excluded from Table 2/Table 12's cross-budget comparison. The reported transfer tally is **68/77**; I counted 77 rows and 68 positive differences in Table 12. Different denominators in Tables 2 and 4 reflect different evaluated sets, not automatically a contradiction.
- Table 4 now reports NAS-refined above uniform in **68/74**, and matching or beating Winner in **49/71** comparable cells. Winner beats uniform in **62/71** of that set.
- Calibration analysis expands to **18/54 correct picks on LongBench** and **19/20 on RULER**. Section 4.2 now explicitly notes seven very small wins below +0.25, alongside the four small losses.
- The corrected Table 8 now reports **20/54** LongBench cells with at least one dataset regression, including **16** with positive category means. Section 4.2 and Appendix A.1 use the updated counts too. The erroneous H2O Single-Doc B128 NAS-refined-based row has been removed, resolving the previously identified Table 8 inconsistency at the manuscript level.
- Table 9's caption now explicitly explains that its calibration ranking compares candidates scored during Stage 4: H2O Single-Doc B128's Stage 3 Winner (29.72, the final result) has no calibration score and is excluded. This addresses the apparent disagreement with the cell's final selection; the calibrated subset's best is not being claimed to be the full final-pool optimum.
- Stage 2 coverage increases to 169/241 points above the uniform curve and 15/16 covered winner panels. Figure 3/Section 5.1 updates the allocation-origin analysis to 41 allocations and 23 search-derived allocations while preserving the dependence caveat.
- The previously corrected EvolKV expansion description, full-workflow attribution, comparison scope, and decoder/shortlisting documentation remain credited. The EvolKV comparison and capped-compute evidence are materially unchanged.

### Ratings

| Dimension | Current score | Assessment |
|---|---|---|
| Overall | **3/5 — Findings** | A useful descriptive allocation/calibration study with broader coverage. The new cells strengthen the existing empirical contribution but do not yet establish a sufficiently stronger novelty/impact case for a main-conference recommendation in my judgment. |
| Soundness | **3.5/5** | Dependence and protocol differences are disclosed, B128 floor matching improves, and the Table 8 error is corrected. Independent evaluation remains absent; the Figure 3/Table 19 best-configuration mismatch needs correction. |
| Excitement | **3/5** | Interesting allocation and calibration patterns; controlled comparative contribution and practical impact remain unestablished. |
| Reproducibility | **3/5** | The algorithm and evaluation are substantially specified, but unavailable archives/settings, subjective stopping, stochastic search, and run-artifact gaps remain. |
| Reviewer confidence | **4/5** | Manuscript/tables checked; no raw-results or implementation audit. |

These are hypothetical reviewer judgments, not acceptance predictions or score thresholds. Broader reporting does not by itself remove selection dependence, and disclosures should not be penalized merely for being candid.

### Current issues to fix before submission

1. **Table 8 inconsistency resolved; related Figure 3/Table 19 mismatch remains.** Table 6 gives H2O Single-Doc B128 uniform 28.21, Winner 29.72, NAS-refined 28.32, and final gain +1.51. Table 8 no longer includes this cell and now uses 20/54 and 16 positive-mean regression counts; the earlier specific objection is closed. However, Figure 3(b), visually checked on PDF page 7, still labels H2O Single-Doc B128's best full-data configuration as NAS-refined. Table 19 likewise calls NAS-refined the best and reports 9/32 layers at the floor. Those best-configuration descriptions conflict with Table 6. Use the Winner vector in the plot/floor table, or explicitly change the scope of the plot/table and associated analysis. If the displayed vector is replaced, recompute any affected Figure 3(a)/Section 5.1 layer frequencies and origin counts; do not assume a label change alone suffices. This is a reporting/analysis consistency check, not a confirmed implementation error, and not the now-resolved Table 8 objection repeated.
2. **Risk discussion still absent in the compiled PDF.** The current 22-page PDF has Limitations but no explicit ethical, societal, or environmental risk discussion. Reporting GPU-hours is not the same as discussing environmental impact. For the checklist question supplied by the user, the earlier recommendation of No with an honest elaboration remains appropriate unless such a discussion is added and compiled. This documentation gap alone does not lower my overall score. Potential topics include search's environmental cost, deployment quality regressions, and dual use of cheaper inference; avoid claiming emissions or safety effects were measured.
3. **Previous minor writing suggestions persist:** Section 1's +1.3–2.1 margin needs its B256–B1024 qualifier and a Single-Doc B256 exception; Section 6 still says within noise without uncertainty evidence; Appendix D still points to Table 14 rather than Table 15 for the capped comparison; the Code B128 delta should preserve lower-bound notation; the decoder should explicitly parameterize the legacy floor; Figure 4's not-used-for-main-results description should identify whether it is a separate run; floor-independent should distinguish final-vector feasibility from search-path independence; restarted initial designs should not be called genuinely guided proposals without qualifying the archive-row convention; full-data selection essential should be scoped to the retrospective protocol.

### Evidence needed for a stronger main-conference case

Independent frozen-allocation evaluation, a focused controlled comparison with comparable data/compute access, and repeatability/uncertainty evidence remain the most important additions. Measured memory/latency/throughput and search-cost amortization would particularly strengthen an MLSys submission. The paper explicitly leaves independent evaluation to future work; no new such results are present in this version. Not all extensions are mandatory, and a seed/heuristic winning remains a valid output of the complete search.

## Retained historical review — October 1, 14:34:16 PDF

The following assessment is retained as history. Its counts (63/67, 68/78, 17/48, etc.) are superseded by the October 3 assessment above. Closed objections remain closed; the historical text is not a second current review.

### October 1 revision: assessment and corrections to earlier review entries

This section records the current assessment. Historical table numbers in the retained earlier review refer to the preceding PDF: the current capped-compute table is Table 15 (formerly 13), the search-cost table is Table 14 (formerly 12), and the comparison summary is Table 23 (formerly 21). Transfer results are now Table 13; Tables 8 and 20–22 give dataset regressions and RULER breakdowns.

**Changes credited in the 14:34 revision:**

- Section 1 explicitly defines the contribution as a complete workflow built from established components. It explains joint layer optimization, unconstrained budget–score exploration, shared rescaling, optional refinement, and full-data selection, without claiming isolated optimizer superiority.
- Section 3.2 explicitly separates improvements on evaluated examples, complete-protocol comparisons, and untested unseen-example generalization. The abstract and conclusion retain the dependence disclosure.
- Section 6 and Tables 14, 15, and 23 distinguish actual costs, the 200-evaluation projection, and capped prefixes. Captions now identify the Code B128 lower bound and exclude upstream Stages 1–2 explicitly. Section 6 goes further: including upstream costs gives at least 75.3 versus 53.7 GPU-hours for the six-cell per-budget protocol. The earlier missing-total-cost qualification is now answered by a disclosed lower bound, although exact Code Stage 1 cost remains unknown.
- Appendix J specifies proportional redistribution among free layers, cap-before-floor clamping, a positive weight floor, largest-remainder rounding, and stable lower-index tie-breaking. The earlier request for these algorithm details is resolved.
- Appendix J specifies the initial-design order and seed 43, surrogate architecture/defaults, unseeded MLP/DE randomness, run-specific watchdogs, candidate-shortlisting groups, legacy RULER shortlists, restart handling, and unavailable records. The earlier assertion that shortlisting and watchdog details are simply absent is no longer current.
- Section 5.1 acknowledges that the 34 allocations are not independent, decomposes their origins, and adds a 19-search-derived-allocation analysis. This is useful descriptive analysis, not repeated-seed evidence; Stage 4 remains seeded by its anchor.
- Section 5.1 correctly identifies both H2O B128 and B1024 transfer exceptions and compares transfer with the receiving method's final configuration. The earlier missing-B1024-exception objection is closed.
- The abstract and Sections 4.2, 4.3, and 5.2 contextualize weak uniform baselines and dataset-level regressions. New Table 8 identifies 17/48 LongBench cells with at least one dataset regression, including 13 whose category mean improves. The earlier context objection is substantially resolved.

**Current ratings:** overall 3/5 (Findings), soundness 3.5/5, excitement 3/5, reproducibility 3/5, confidence 4/5. Reproducibility is now near the stronger end of 3: the procedure is much better specified, but lost archives, unavailable settings/timings, unseeded stochastic search, subjective stopping for some runs, and missing released run vectors/shortlists still impede exact replication. These are not claims of implementation errors. A cleaner reference protocol and reproducible artifacts could support 4 without requiring a new scientific hypothesis.

**Remaining writing-only suggestions (minor; not independent rejection grounds):**

1. In Section 1, restrict the +1.3 to +2.1 Code margin to B256–B1024, and mention the Single-Doc B256 loss rather than saying simply that MOSAIC matches EvolKV. Section 6 already gives the correct qualification.
2. Replace “within noise” in Section 6 with a numerical description unless measured uncertainty is supplied. The current comparisons have no uncertainty estimate demonstrating equivalence.
3. Appendix D still calls Table 14 the matched-cost comparison in one sentence; the capped comparison is Table 15. Use at least +0.81, not an exact +0.81, for the Code B128 difference in Table 15 and related summaries.
4. Explicitly parameterize Appendix J's decoder by the run's floor (16 or 64); its feasibility condition currently names 64. Clarify whether Figure 4's “not used for the main results” configurations are from a separate run, since the main table also contains floor-16 SnapKV B1024 results.
5. Qualify “floor-independent” for B1536/B2048: a final configuration not touching 16 does not prove the search or allocation would be unchanged under floor 64. Show the minimum is at least 64 if claiming the final vector is feasible under both floors, and distinguish feasibility from search-path independence.
6. Do not label all rows after 63 as genuinely guided proposals if restarted initial designs are appended there. Appendix J discloses this bookkeeping convention, but the headline 25/67 origin count needs that qualification or an actual-origin recount from existing logs.
7. Frame “full-data selection essential” as a finding about this retrospective protocol, not proof that selecting on reported test examples is the only remedy for unreliable calibration rankings. Larger or better-designed independent validation is an alternative.

**Evidence gaps relevant to moving toward main conference:** frozen-allocation evaluation on unseen examples; a focused controlled comparison isolating the central workflow advantage; uncertainty/repeated-search evidence for small differences; and measured inference benefits or compelling evidence of practical usefulness. These are separate from the closed wording concerns. Not every extension is compulsory: prioritize the experiment that best supports the paper's central claim.

## Retained historical review — 12:01:59 PDF

The material below is preserved as revision history, not a second assessment of the 14:34:16 PDF. Its unresolved wording/specification comments are superseded by the latest assessment above; in particular, redistribution/tie-breaking, shortlisting/watchdogs, allocation dependence, transfer exceptions, cost captions, and weak-baseline context have since been answered. Historical ratings and table numbers below refer to that earlier version. The latest review covers the current PDF and appendices; experiment code, archives, and raw predictions were not audited, and the paper/source were not edited.

### Historical scope and overall assessment

This review covers the manuscript and appendices. The published EvolKV paper was checked to assess the related-work and amortization claims. Experiment code, raw predictions, and search archives were not audited. Implementation concerns below are therefore checks to perform, not findings of confirmed implementation bugs. The paper and its source files were not modified.

The manuscript contains promising empirical evidence that reallocating cache across layers can improve particular eviction methods, especially on RULER. Its coverage of four eviction methods, cross-budget results, and analysis of calibration rankings are useful strengths.

Several earlier criticisms have been addressed. The paper explicitly limits its evaluation to the examples used for selection, correctly describes EvolKV's cross-budget expansion, and defines NAS-refined as the output of the complete Stage 4 search. A search may legitimately return a configuration from its initial design; the winner does not have to originate from a guided BO proposal. The review must not continue treating corrected wording or initial-design winners as defects.

The updated Section 3.2, Table 2 caption, and Appendix J resolve the search-grid contradiction by documenting the wider grids used for L2Norm and H2O Code. Section 1, Section 6, and Table 21 correctly distinguish joint optimization from blockwise optimization of individual layer budgets. Table 21 retains an explicit selection-dependence caveat. The cost comparison now separates search-once and per-budget protocols, adds Stage 2 costs, and acknowledges the seed's upstream cost. These are substantial improvements that support a narrowly positive Findings recommendation for the descriptive empirical contribution.

The new Table 13 and Appendix D substantially address the remaining normalized-cost objection. They distinguish the 51.1 GPU-hour projection from the actual searches, add final re-evaluation costs (84.9 GPU-hours total as run), and reconstruct prefixes capped at EvolKV's per-cell budgets. Those prefixes plus reserved re-evaluation cost total 47.2 GPU-hours. Five reported configurations are already in the initial design and remain available; Code B128 becomes an explicit lower bound of at least 55.73. This supports the stated 5/6 descriptive win count within the reported incremental Stage 4 caps. It does not establish that the complete pipeline costs less: obtaining the Winner seed incurs the separately acknowledged Stages 1–2 cost.

Remaining suggestions concern the incomplete guided-candidate re-evaluation at Code B128, reproducibility of prefix/shortlist cost calculations, legacy-floor decoding, uncertainty, and several local wording inconsistencies. Independent evaluation remains explicitly absent; the findings retain their stated scope of performance on examples used for selection.

## Current reviewer recommendation

**Overall: 3/5 — Findings, unchanged but better supported. Soundness: 3.5/5, up from 3/5. Reproducibility: 3/5, unchanged.** This is a hypothetical reviewer assessment, not a prediction of the eventual ARR decision. The categories follow the [ARR review form](https://github.com/acl-org/aclrollingreview/blob/main/reviewform.md).

| Dimension | Current score | Reason |
|---|---|---|
| Overall | 3/5 | A positive Findings recommendation for the empirical allocation/calibration contribution, strengthened by the capped-compute analysis. Novelty, robust generalization evidence, and practical impact do not yet justify a conference-level score in my assessment. |
| Soundness | 3.5/5 | The capped-prefix analysis substantially resolves the remaining compute comparison objection at the incremental Stage 4 scope. One score remains a lower bound, and independent generalization and total-cost superiority are not established. |
| Excitement | 3/5 | The allocation results and calibration-ranking analysis are interesting; the incremental advantage over existing allocation search still needs careful interpretation. |
| Reproducibility | 3/5 | The grids, decoder, evaluation settings, calibration fractions, and attention backend are documented; legacy floors, lost logs, and remaining run-specific details still make exact replication difficult. |
| Reviewer confidence | 4/5 | Main claims and tables checked against the updated PDF and relevant EvolKV description; no execution or raw-results audit. |

The earlier overall increases credited the expansion baseline, corrected grids, and clearer protocol accounting. The current soundness increase credits new evidence about candidates available within compute caps, not merely different wording. The expansion comparison remains unchanged: Winner leads expanded EvolKV in 5/6 cells at B256–B1024. The new capped Stage 4 comparison also wins 5/6 cells, with Code differences of at least +0.81, +0.99, and +1.71 and Single-Doc differences of +0.17, −0.67, and +0.61. These remain descriptive differences under the disclosed selection protocol.

The current 3/5 assessment judges the paper as an empirical study of searched allocations on the evaluated examples. Its contribution is now supported well enough for Findings in my judgment. Candidate origins are valid, the main specification contradictions are corrected, and the latest comparison measures availability within per-cell compute caps. A conference-level recommendation would need a stronger case for novelty, reliable advantages on unseen examples, or practical impact; completing an individual reviewer correction does not by itself establish those additional strengths.

### Changes credited in this version

- New Table 13 uses evaluation-order prefixes capped at each EvolKV run's compute cost and includes the full-data re-evaluation budget. It reports actual run costs, winner discovery indices, capped evaluation counts, capped costs, and capped scores.
- Appendix D explicitly labels 51.1 GPU-hours as a projection rather than the cost of the configurations reported. Actual Stage 4 search plus final re-evaluation totals 84.9 GPU-hours; capped prefixes total 47.2 against EvolKV's 53.7, before the separately acknowledged seed cost.
- Five configurations are already present in the 64-point initial design. Code B128's later winner is excluded by the cap, and the replacement is reported as a lower bound (at least 55.73), rather than incorrectly retaining 56.09.
- The Code B128 within-prefix guided proposal has not been re-evaluated. The lower-bound notation makes that incompleteness explicit; archive/shortlist provenance would make the reconstruction easier to audit.
- The corrected grids, blockwise description, optimism caveat, and separate protocol accounting from earlier revisions remain credited below.
- Section 3.2, Table 2, and Appendix J now identify seven levels through 4096 for RULER, L2Norm, and H2O Code, and five levels through 1024 for the remaining LongBench runs. This resolves the earlier impossible-average objection.
- Sections 1 and 6 and Table 21 now explicitly describe EvolKV's individual layer budgets optimized blockwise, with earlier groups frozen, and MOSAIC's joint optimization of all 32 layer budgets. The allocation-granularity objection is resolved.
- Table 21 replaces the assertion that optimism is removed with a qualification that selection and reporting still use the same examples. The earlier summary-wording objection is resolved.
- Section 6, Appendix D, and Table 21 separate search-once and per-budget comparisons. Single-Doc MOSAIC Stages 1–2 cost 16.5 + 3.6 = 20.1 GPU-hours versus EvolKV's 5.2. Code Stage 2 costs 8.0 GPU-hours, with Stage 1 still unrecoverable. The paper also acknowledges that Stage 4 inherits the cost of its Winner seed. This substantially addresses the missing upstream-cost objection.
- The former claim of matched quality based solely on 51.1 GPU-hours is superseded by the explicit capped-prefix Table 13. The remaining limits of that analysis are recorded in Issue 9.
- The improvements below from earlier revisions remain credited.
- Sections 3.2 and 4.1 retain the clarified stage-specific calibration protocol: LongBench Stage 1 uses 30% and Stage 4 uses 10%, while RULER uses 10% in both stages, for all four methods. Table 1 and Appendix B remain aligned with this account.
- Appendix J now specifies FlashAttention-2 for all four methods. The earlier assertions that L2Norm's calibration fraction and AdaKV's attention backend were unrecorded are no longer current manuscript objections. The earlier L2Norm SDPA description has also been replaced.
- The added rationale for a larger once-per-task Stage 1 subset and a smaller per-budget Stage 4 subset helps explain the design. It is a design rationale, not a new controlled experiment establishing that these fractions are optimal.
- Appendix J specifies normalized continuous decoding, clipping/redistribution, largest-remainder integer rounding, and the affine map used to seed/rescale the Stage 2 winner. This substantially addresses the earlier missing-decoder objection.
- Appendix J supplies precision, greedy decoding, context truncation, output lengths, scoring metrics, calibration sampling seed, attention implementation, and hardware details.
- Section 6 retains MOSAIC's selection sizes (1,000 Code / 550 Single-Doc examples) and EvolKV's 30-example selection size, with an explicit attribution caveat. Table 21 now preserves the evaluation-dependence caveat too.
- From the preceding revision, Section 6/Table 5 adds the previously missing search-once-and-expand baseline and explicitly reports the Single-Doc B256 loss.
- The reported final-result coverage increases from 60/64 to 63/67 wins over uniform; Stage 3 transfer coverage increases from 67/77 to 68/78.
- Table 4 now reports NAS-refined above uniform in 62/67 cells and matching or beating Winner in 47/66 comparable cells.
- Section 5.1 adds the last planned Code cross-method transfer point, SnapKV to H2O at B1024 (57.05), completing the six budget/direction configurations. Its comparison with H2O's own Winner needs a label correction (Issue 10).

## Revision assessment

| Concern | Status in the revised PDF | Reviewer assessment |
|---|---|---|
| Selection dependence and Stage 3 interpretation | Reporting concern substantially addressed in the abstract, Section 3.2, Table 5, conclusion, and Limitations item 1 | The paper now explicitly distinguishes budget transfer on evaluated examples from unseen-example performance. |
| Stage 3 described as least biased or as a fair independent comparison | Addressed | The earlier smallest-bias claim and fair-comparison wording have been removed. |
| Independent held-out evaluation | Still absent; explicitly acknowledged | Required to establish unseen-example performance, but its absence does not invalidate descriptive findings on the evaluated examples. |
| EvolKV said to require a new search at every budget | Resolved in Sections 2.1, 3.2, and 6 | The paper now acknowledges expansion without further optimization and shared amortization. |
| Comparison against EvolKV's expansion protocol | Added; earlier missing-experiment objection resolved | Section 6/Table 5 compares both search-once outputs. Selection-policy comparability, reproduction detail, and end-to-end cost remain qualifications, not absence of this baseline. |
| Unequal data access in the EvolKV comparison | Reporting concern addressed in Section 6 and Table 21 | The imbalance and potential source of gains remain explicit; the optimism row now preserves selection dependence. |
| Decoding, rescaling, rounding, and evaluation settings | Substantially addressed in Appendix J | Remaining details concern redistribution weights, legacy floors, and run-specific provenance, rather than a missing decoding description. |
| L2Norm calibration fraction and AdaKV attention backend | Documentation concerns addressed | The current PDF gives stage-specific fractions for every method and FlashAttention-2 for all four; historical run settings have not been independently audited. |
| New introduction and comparison table | Main granularity/optimism/protocol objections addressed | Comparison now uses capped Stage 4 costs; remaining suggestions concern the lower-bound score and local performance summaries. |
| Stage 1 grid and reported anchor budgets | Resolved | Method-specific seven-level grids explain averages above 1024. |
| Upstream cost and protocol alignment | Substantially addressed | Separate protocol blocks and Stage 2 costs remain; new Table 13 caps the incremental search/re-evaluation budget. Total Code Stage 1 cost remains unknown. |
| Normalized cost attached to uncapped quality | Substantially addressed by new Table 13 | Actual prefixes replace the projection-based comparison; Code B128 is a disclosed lower bound and seed costs remain additional. |
| Search winners attributed specifically to guided BO | Resolved by the NAS-refined definition in Section 3.2, Table 4, and Limitation 7 | Initial-design configurations are valid outputs of the complete search. Component isolation is an ablation suggestion, not an automatic rejection reason. |
| Final MOSAIC configuration versus uniform baseline | Reporting definition clarified | The method and tables use the better of Winner and NAS-refined; Figure 3 separately shows the best evaluated configuration including uniform. |
| Mechanistic explanation of task differences | Hypothesis-framing concern addressed | Section 5.2 explicitly calls evidence localization an untested hypothesis. Independence and transfer scope still need care. |
| Cross-method transfer coverage | Six planned Code configurations reported; explicit numeric mislabel removed | The B128 exception is now acknowledged, but the generic Winner comparison still needs a B1024 qualification (Issue 10). |

## Priority overview

| Issue | Current status / priority | Main locations |
|---|---|---|
| 1. Selection dependence | Interpretation substantially addressed; held-out evidence remains a scope limitation | Abstract, Section 3.2, Table 5, conclusion, Limitations item 1 |
| 2. EvolKV | Factual correction and missing expansion experiment resolved; comparison qualifications remain | Sections 2.1, 3.2, and 6; Table 5 |
| 3. Search attribution | Candidate-origin/naming objection resolved; component ablation is a supporting experiment | Section 3.2, Table 4, Limitation 7 |
| 4. Search grid and winner budgets | Resolved in manuscript specification | Section 3.2, Table 2 caption, Appendix J |
| 5. Final configuration definition | Reporting inconsistency substantially resolved | Section 3.2, Figure 3, Tables 3–7, Appendix A |
| 6. Rescaling and floor handling | Decoder substantially documented; legacy-floor consistency and minor algorithm details remain | Section 3, Table 3, Figure 4, Appendices E and J |
| 7. Experimental provenance | Partially addressed; evaluation settings supplied, some run metadata still unavailable | Section 4.1, Limitations, Appendices D and J |
| 8. Uncertainty | Open for robustness/significance claims | Tables 4–7 and headline win counts |
| 9. Search cost | Previous normalized-cost objection substantially addressed; lower-bound/provenance and total-cost qualifications remain | Section 6, Appendix D, Tables 12–15 and 21 |
| 10. Interpretation and transfer | Mechanistic wording improved; independence/scope concerns remain | Sections 5.1–5.2, Figure 3, conclusion |
| 11. Weak-baseline context | Contextual recommendation / medium | RULER results and Section 5.2 |
| 12. Systems evidence and broader coverage | Claim-dependent recommendations | Experimental setup and main results |

## 1. Evaluation interpretation corrected; held-out evidence remains absent

**Status: Reporting/interpretation concern substantially addressed. Remaining limitation: performance on unseen examples has not been established.**

The current abstract explicitly states that scores use benchmark examples involved in selection and that held-out evaluation is future work. Section 3.2 explains that Stage 3 inherits its anchor's selection dependence and measures transfer across budgets on those examples. Table 5 no longer calls Winner a fair independent comparison. The conclusion is scoped to the evaluated benchmark examples, and Limitation 1 describes what an independent evaluation would require.

These corrections should be credited. The prior objections about an omitted abstract caveat, an unsupported smallest-bias claim, and the fair-comparison caption are no longer current. The existing experiments can support descriptive findings about which searched allocations perform well on the observed samples. Lack of a held-out test does not, by itself, make that narrower descriptive study invalid.

The remaining limitation is that the observations do not establish performance on unseen examples. Selecting a shape using examples D and rescaling it to another budget still produces a configuration dependent on D. For the calibration-selected exceptions, an independent evaluation must likewise exclude the calibration examples.

One wording issue remains: the abstract and method still describe full-data selection as essential. The calibration analysis shows unreliable rankings on the sampled subsets; it does not establish that selection on the same reported evaluation examples is the only solution. Frame this as the protocol used for the retrospective analysis, or motivate stronger validation instead of necessity.

If extending the claims to generalization:

- Separate search, validation, and final test examples before the relevant selection steps.
- Freeze allocations before testing; independently generated RULER examples offer a practical evaluation route.
- For LongBench, rerun the relevant search and selection stages without the held-out examples.
- Apply comparable data access and selection rules to baselines.
- Report independent scores and uncertainty estimates rather than reusing selection-conditioned scores.

Removing calibration examples from an existing score does not undo full-data Stage 2/4 selection. A nominal test subset carved out after its examples influenced selection is not retroactively untouched. If the paper retains its current retrospective scope, keep that scope explicit throughout instead of implying unseen-example performance.

## 2. EvolKV factual correction and missing expansion experiment resolved

**Status: The previous factual error and missing-expansion-baseline objection are resolved. Remaining concerns concern interpretation and protocol detail.**

Sections 2.1 and 3.2 now acknowledge that EvolKV optimizes at one budget and expands its allocation without further optimization. Section 6 distinguishes the direct-optimization setting used in the reproduction from the expansion protocol, and acknowledges that both methods can amortize a search across budgets. This is consistent with the relevant published description. [EvolKV, Section 4.2.1 and Appendix C.4](https://aclanthology.org/2025.findings-emnlp.88.pdf)

Section 6 and Table 5 now include both direct EvolKV searches and an allocation searched at B128 then expanded to B256, B512, and B1024 without further optimization. The corresponding MOSAIC Winner is also searched once and rescaled. The earlier assertion that this experiment remains to be run is no longer true.

The six expanded-budget comparisons are:

| Task | Budget | Expanded EvolKV | MOSAIC Winner | Winner minus expanded |
|---|---:|---:|---:|---:|
| Code | 256 | 55.99 | 57.33 | +1.34 |
| Code | 512 | 56.82 | 58.16 | +1.34 |
| Code | 1024 | 56.42 | 58.52 | +2.10 |
| Single-Doc QA | 256 | 35.43 | 34.51 | −0.92 |
| Single-Doc QA | 512 | 36.14 | 36.33 | +0.19 |
| Single-Doc QA | 1024 | 36.38 | 36.46 | +0.08 |

This is substantive evidence in favor of the proposed framework, especially on Code, and supports raising the overall score. It does not establish statistically reliable superiority on Single-Doc QA.

Remaining qualifications:

- Section 6 explicitly acknowledges unequal selection-data access: MOSAIC selects on 1,000 Code / 550 Single-Doc examples, whereas EvolKV searches and selects on 30 examples per task. The former sample-count table is gone, but the disclosure remains in the text and the new Table 21 summarizes the selection rules. The stated 30% Stage 1 protocol corresponds to 300 / 165 search examples on these dataset totals; Stage 4 uses 100 / 55. The comparison remains one of complete protocols on the evaluated samples, not an isolated optimizer or allocation-space advantage. Matched selection would be needed to establish that narrower attribution, not merely to report the present descriptive results.
- Section 6 now explicitly says that the eight separate per-layer budgets in each EvolKV group are optimized in turn, with earlier groups frozen. Sections 1 and 6 and Table 21 resolve the prior granularity ambiguity in the manuscript. Implementation fidelity was not audited; that normal audit boundary is not a newly asserted defect. [EvolKV, Section 3.2 and Algorithm 1](https://aclanthology.org/2025.findings-emnlp.88.pdf)
- Table 5's data-overlap statement applies to this reproduction. The published EvolKV evaluation removes its optimization examples; do not imply that the original paper reported the same overlapping-data protocol. [EvolKV, Section 4.2.1](https://aclanthology.org/2025.findings-emnlp.88.pdf)
- Search-once costs are reported in Section 6, Appendix D, and Table 21: 20.1 versus 5.2 GPU-hours for Single-Doc, and 8.0 GPU-hours for MOSAIC Code Stage 2 versus 12.7 for EvolKV's Code search, with MOSAIC Code Stage 1 unavailable. This addresses the missing protocol-cost account where records exist. The new capped incremental comparison and its remaining limits are discussed in Issue 9.

### Introduction and Table 21: resolved concerns and remaining qualifications

- **Allocation granularity:** Resolved. The text and table now correctly describe both methods as assigning a budget to each layer, with blockwise optimization in EvolKV and joint optimization in MOSAIC.
- **Optimism wording:** Resolved. The MOSAIC entry now states that selection and reporting share the same examples. This correctly preserves the dependence caveat while explaining that reported results use full-data scores rather than optimistic calibration estimates.
- **Performance summary:** The introduction's Code margin of +1.3 to +2.1 applies to B256–B1024; if “every budget” also includes B128 in Table 5, that margin is +0.94. The Single-Doc summary should mention the B256 loss of −0.92 and small positive margins at B512/B1024, rather than suggesting demonstrated equivalence at all budgets.
- **Scope of prior-work coverage:** The table now says “methods tested” and “benchmarks tested”; explicitly identify these as the experiments in this manuscript so readers do not infer that the published EvolKV study had only this local reproduction's coverage. This is a clarity suggestion rather than an independent rejection reason.
- **Search cost:** The table separates quality and cost by protocol, acknowledges the seed's upstream cost, and now uses capped-prefix results rather than uncapped results paired with a projection. This substantially resolves the former comparison objection. The lower-bound/provenance qualifications in Issue 9 remain.

## 3. Search-output naming and candidate-origin concern resolved

**Status: Resolved for reporting the complete Stage 4 procedure. Component isolation is now an ablation suggestion, not an automatic rejection reason.**

Section 3.2, Table 4, and Limitation 7 now use NAS-refined for the selected output of the full Stage 4 procedure, including its initial heuristic/LHS configurations. A search can legitimately return its best evaluated configuration from initialization. It is not required to return a configuration produced by a guided BO iteration.

The earlier review gave too much weight to where winning configurations originated. The previous statement that BO won only 3/20 cells referred to the earlier guided-proposal breakdown; it must not be presented as a description of the current NAS-refined column. The current Table 4 reports NAS-refined above uniform in 62/67 cells and matching or exceeding Winner in 47/66 comparable cells, subject to the paper's disclosed selection protocol.

This establishes the reported outcome of the complete procedure on the evaluated samples. It does not isolate the incremental effect of guided iterations, but such isolation is not required merely to use an existing optimizer within a framework and report that framework's output.

Useful supporting experiments, depending on the claims:

- To attribute gains specifically to guided BO, compare guided and unguided proposals starting from the same initial design and using the same total evaluation budget.
- To assess end-to-end search efficiency, compare the complete procedure against a simpler search alternative under comparable compute and selection rules.
- Retain candidate provenance in an appendix or released logs for interpretability and reproducibility; a seed winning is not a defect.

Do not insist on this ablation as a standalone acceptance condition solely because the search uses BO. Judge the novelty and usefulness of the claimed overall framework against appropriate alternatives.

## 4. Stage 1 search-grid contradiction resolved

**Status: Resolved in the manuscript specification.**

Section 3.2 and Appendix J now specify the seven-level grid `{64, 128, 256, 512, 1024, 2048, 4096}` for RULER, L2Norm, and H2O Code, and the five-level grid through 1024 for the remaining LongBench runs. Table 2's caption explicitly explains why some natural budgets exceed 1024.

The H2O Code anchor at 2456 and L2Norm Summarization anchor at 2518 are therefore consistent with the documented maximum of 4096. The prior impossible-average objection is closed and is a principal reason for the rating increase. Saved vectors/logs would still help exact replication, but their absence is a separate provenance limitation rather than a reason to retain the resolved contradiction.

## 5. Final configuration and uniform-reference distinction clarified

**Status: Earlier reporting inconsistency substantially resolved.**

Section 3.2 now defines the final MOSAIC result as the better of Winner and NAS-refined. Tables 3 and 5 and Appendix A follow that convention. Figure 3 is separately labelled as the best full-data configuration per cell and can therefore show uniform where uniform is better than either reported MOSAIC configuration.

This resolves the earlier contradiction between a final result supposedly selected from a pool including uniform and a final result that loses to uniform. The distinction between the reported MOSAIC result and Figure 3's best evaluated allocation is now explicit.

Retain this distinction in future revisions. For reproducibility, also specify the exact calibration-based shortlisting rule before full-data re-evaluation: NAS-refined is selected from that re-evaluated shortlist, not established to be the full-data optimum over every configuration in the entire search archive. This is a specification detail, not the earlier reporting contradiction.

## 6. Rescaling and rounding substantially documented; floor-specific details remain

**Status: The missing-decoder objection is substantially addressed by Appendix J (pages 14–15 in this PDF). Remaining concerns are narrower specification and consistency checks.**

The appendix now states that Stages 3–4 normalize weights to a total of `T = 32B`, clamp budgets to `[64, 4096]`, redistribute the excess/deficit over remaining layers, and use largest-remainder rounding to reach the exact integer total. It specifies the winner mapping as `x_i = 0.05 + 0.9 w_i / max_j(w_j)`, and explicitly acknowledges that this is affine rather than ratio-preserving proportional scaling. It also documents the separate proportional rule used for the expanded EvolKV baseline. These are meaningful answers to the earlier question and should be credited.

The abstract, Figure 1, and Appendix C now avoid the earlier claim of exactly proportional winner rescaling. Layer ranking can be preserved up to clipping/rounding ties, but relative budget ratios generally change; the new affine-map explanation makes that distinction clear.

Remaining clarifications:

- Parameterize the decoder by the run's actual lower bound. Appendix J currently describes `[64, 4096]` without explaining how that decoder changes for the floor-16 results in Table 3. At B64 with a floor of 64 only uniform is feasible; the nonuniform B64 results necessarily use the documented legacy floor-16 setting. This is a consistency issue between the general appendix algorithm and those runs, not evidence of an implementation bug.
- Specify whether redistribution over unconstrained layers is proportional to their weights or equal, and give a deterministic tie rule for largest-remainder rounding. Brief pseudocode would remove this residual ambiguity; the review should no longer claim that clipping or integer rounding is entirely unspecified.
- Figure 4 still says its floor-16 example is not used for the main results, while Table 3 includes floor-16 SnapKV RULER B1024 results. Clarify whether the plotted candidates come from a separate exploratory run. Matching floor and budget alone do not prove identical configurations.
- Link the saved winner/final budget vectors to the relevant run settings so readers can check the totals and bounds.

## 7. Evaluation metadata substantially improved; some run provenance remains missing

**Status: Substantially improved documentation; some run-provenance gaps remain. Reproducibility remains 3/5, unchanged from the preceding review.**

Appendix J supplies float16 precision, greedy single-beam decoding, the prompt/chat-template convention, the 7,500-token middle-truncation rule, output-length range and task metrics, SnapKV pooling/window settings, calibration sampling using `random.Random(42).sample`, FlashAttention-2 for all four methods, and hardware assignments. Sections 3.2/4.1 now specify calibration fractions by stage for every method. The review should no longer ask for these as if absent.

The current PDF no longer leaves L2Norm's calibration fraction or AdaKV's attention implementation unspecified. Earlier versions described AdaKV Stage 4 as using 30%, left L2Norm's fraction unknown, and described L2Norm as using SDPA; the current account replaces those statements with Stage 4 at 10% and FlashAttention-2 throughout. These are credited as corrections to the manuscript, not independently verified facts about the historical runs: experiment code and logs were not audited. A short provenance note explaining whether these correct earlier descriptions or reflect reruns would help readers reconcile versions; no implementation error is asserted.

The Stage 1 grid is now consistent with the reported anchor means. Remaining reproduction obstacles are lost Stage 1 logs, incomplete run-specific vectors/shortlists and stopping details, legacy floor/winner-selection differences, and the still-running AdaKV Summarization entry. The new documentation helps reproduce the procedure but does not reconstruct those missing run records.

Recommended remaining work:

- Release the dataset ordering/revision or sample IDs, saved winner vectors, per-run grids/floors, candidate shortlists, and relevant library/code versions.
- Make the watchdog/manual stopping and calibration shortlisting rules reproducible, or clearly separate exploratory runs from a fixed reference protocol.
- Recover missing metadata where possible; do not silently replace an unknown historical setting with the current code default.
- Complete pending experiments or remove unfinished placeholders and define the final evaluation scope.

## 8. Small gains and win counts need uncertainty estimates

**Priority: High.**

Many LongBench differences are fractions of a point. Positive differences such as +0.01 or +0.04 should not carry the same evidential weight as large, repeatable gains. An exact win count on the selected benchmark examples is a valid descriptive statistic; interpreting it as robust superiority beyond those examples requires additional evidence.

The manuscript also calls some differences within run-to-run noise without presenting repeated-run evidence that quantifies that noise. Search randomness and finite evaluation samples are distinct uncertainty sources.

Recommended resolution:

- Repeat representative searches with different seeds and calibration samples.
- Report paired confidence intervals for test-score differences, using a procedure appropriate to the task aggregation.
- Show effect sizes alongside win counts.
- Avoid treating budget cells that reuse the same allocation and examples as independent replications.
- For generalization claims, compute uncertainty on independent evaluation after the relevant selection steps. Confidence intervals on already selected test winners do not remove selection bias.

## 9. Normalized-cost objection substantially addressed by capped-prefix analysis

**Status: Substantially addressed in Section 6, Appendix D, and new Table 13. Remaining qualifications concern the Code B128 lower bound, provenance, and the scope of the compute comparison.**

Appendix D now explicitly identifies 51.1 GPU-hours as a projection rather than the cost of the reported configurations. The six actual Stage 4 searches take 76.9 GPU-hours, plus 8.0 for full-data re-evaluation of three candidates per cell, totalling 84.9. New Table 13 caps each search prefix at its corresponding EvolKV run's GPU-hour cost and reserves the re-evaluation cost. Initial designs are included, and the cap covers all 64 initial points. The capped search/re-evaluation total is 47.2 GPU-hours against EvolKV's 53.7.

| Cell | Reported run score | Available capped score | EvolKV | Capped difference |
|---|---:|---:|---:|---:|
| Code B128 | 56.09 | ≥55.73 | 54.92 | ≥+0.81 |
| Code B512 | 58.01 | 58.01 | 57.02 | +0.99 |
| Code B1024 | 58.91 | 58.91 | 57.20 | +1.71 |
| Single-Doc B128 | 33.67 | 33.67 | 33.50 | +0.17 |
| Single-Doc B512 | 35.61 | 35.61 | 36.28 | −0.67 |
| Single-Doc B1024 | 37.01 | 37.01 | 36.40 | +0.61 |

Five reported configurations were found in the initial heuristic/LHS design and therefore remain available within the caps. Code B128's original winner appeared at evaluation 454, outside the capped prefix ending at 151. The paper replaces its score with a disclosed lower bound based on an already re-evaluated candidate available in that prefix. This is a substantive answer to the earlier request to compare candidates actually available under a compute budget. Initial-design candidates remain valid search outputs; their origin is not a defect.

The Code B128 guided candidate that the capped protocol would shortlist has not been re-evaluated. Thus ≥55.73 should remain a lower bound, with the identity, archive index, shortlist category, and full-data score of the already evaluated fallback candidate made explicit. Assuming the documented shortlist retains that eligible candidate, this suffices to establish the descriptive win over 54.92; it does not establish the exact full-data output of the capped guided search. Re-evaluating the missing candidate would complete that cell, but the review should not continue describing the comparison as merely a normalized-cost projection.

Remaining scope and reporting suggestions:

- Keep the comparison labelled as incremental Stage 4 search plus final re-evaluation. The one-time Stages 1–2 needed to obtain the Winner seed are explicitly additional; the analysis does not establish lower total pipeline cost than EvolKV.
- Retain the separate one-time costs: MOSAIC Single-Doc is 20.1 versus EvolKV's 5.2 GPU-hours. MOSAIC Code Stage 2 is 8.0, but its total remains unknown because Stage 1 logs were lost.
- Release the prefix-cost calculation and exact shortlisted candidate IDs. Some original timings are estimates; use the same measured-versus-estimated distinction for derived cap costs.
- Appendix D still calls Table 12 the matched-cost comparison in one sentence, although Table 12 contains projections and Table 13 supplies the capped results. Point that sentence to Table 13.
- Table 13's caption could identify the Code B128 entry as a lower bound and make the ≥ sign explicit in its difference column, consistent with the score column and explanatory text.

This improvement raises soundness to 3.5/5 while the overall Findings recommendation remains 3/5. Robustness, generalization, and total-cost advantages remain separate questions.

## 10. Mechanistic explanation improved; independence and transfer claims still need care

**Priority: Medium. Status: Partially addressed.**

The revised paper removes the earlier Why Task Type Matters explanation about lower-layer retrieval, upper-layer reasoning, and nearly equal layer importance in QA. Section 5.2 now explicitly calls evidence localization an untested hypothesis. This addresses the earlier criticism of those statements as established mechanisms; that criticism should not be carried forward unchanged.

The remaining concern is the interpretation of repeated allocations and limited transfer tests. Section 5.1 begins by saying that each cell is searched independently, but Figure 3 includes multiple rescalings of winner allocations and the winner anchors themselves. These are not independent discoveries of the same layer preference. Similarly, the limited cross-task and cross-method experiments do not establish universal transfer or non-transfer behavior.

The latest PDF completes six Code cross-method configurations: both directions between SnapKV and H2O at B128, B512, and B1024. The new SnapKV-to-H2O B1024 result is 57.05, compared with uniform at 56.92. This completes the previously pending point and deserves credit; Limitation 8 now scopes cross-method transfer to Code rather than describing incomplete coverage.

The latest Section 5.1 removes the explicit mislabelling of 57.23 as H2O's B1024 Winner and acknowledges H2O B128 as an exception to the receiving method's Winner beating the transfer. That is an improvement. However, its remaining statement that the transfer trails the receiving method's own Winner except at B128 still conflicts with the B1024 values retained from earlier revisions: transferred SnapKV scores 57.05, H2O's rescaled Winner scores 56.15, and H2O's NAS-refined configuration scores 57.23. Either give B1024 as another exception or consistently compare with the receiving method's final configuration. This is a local interpretation/caption fix rather than the earlier direct numeric-label error.

Recommended resolution:

- Retain the explicit hypothesis framing for the evidence-localization explanation.
- Distinguish independent searches from reused/rescaled configurations in Section 5.1 and the layer-frequency analysis.
- Check whether middle-layer preferences recur across independent searches if making a stability claim.
- Phrase transfer conclusions as applying to the task and method pairs actually tested.

## 11. Large improvements over weak baselines need context

**Priority: Medium.**

At RULER B1024, L2Norm improves from 35.59 to 67.03, while uniform SnapKV scores 85.67. The L2Norm gain is meaningful evidence that allocation improves that method, but it does not show that the resulting system is competitive with stronger eviction methods at the same budget.

Recommended resolution:

- Distinguish improvement within each eviction method from absolute performance across methods.
- Include a full-cache reference and strong compressed-cache baselines.
- Preserve per-subtask breakdowns so average gains do not hide substantial regressions such as the H2O B1024 CWE drop.

## 12. Practical efficiency and broader applicability remain under-tested

**Priority: Claim-dependent; broader coverage is not a standalone acceptance requirement.**

The experiments use one model, and RULER is evaluated only at 4K context. These facts limit the conclusions' scope, but do not automatically invalidate a study explicitly restricted to that setting. Average tokens per layer is a useful allocation measure; it does not by itself establish measured peak-memory, latency, or throughput benefits.

Recommended extensions where they support the intended claims:

- Measure actual cache/peak memory and inference latency if claiming practical systems improvements.
- Add a second model or additional context lengths if claiming broader applicability; otherwise state the evaluated scope precisely.
- Explain how task-specific searches would be used in deployment and when their cost is amortized.
- Do not prioritize a large-model sweep over resolving the existing search specification and comparative-evidence gaps.

## Recommended order of work

1. Retain and credit the new capped-prefix comparison. Clarify its incremental-cost scope, provide candidate/prefix provenance, and complete the Code B128 guided-candidate score if feasible; keep the lower-bound notation meanwhile.
2. Keep the corrected Stage 1 grids and joint-versus-blockwise distinction closed. Clarify the decoder's legacy-floor parameter, redistribution rule, and shortlisting details.
3. Document the remaining run provenance; retain the explicitly unknown Code Stage 1 cost and the newly reported Stage 2 costs.
4. Keep the now-explicit retrospective scope, or add independent evaluation to support unseen-example performance. Do not describe the corrected reporting as if it were still undisclosed leakage.
5. Add uncertainty and repeated-search evidence where claiming robustness or meaningful small gains.
6. Consider a matched random/LHS comparison as evidence about search efficiency or guided-iteration value; do not require a winner to originate from guided BO.
7. Qualify the Section 5.1 B1024 transfer comparison and the introduction's performance summary; add broader models, contexts, or systems measurements when justified by the intended claims and resources.

Resolved or substantially addressed concerns now include the Stage 1 grid contradiction, EvolKV's expansion capability and individual layer variables, the missing expansion experiment, the optimism caveat, the NAS-refined definition, the final-result convention, the separation of protocol costs, and the replacement of projection-based quality claims with capped-prefix evidence. Decoder/evaluation settings, calibration fractions, attention backend, and Stage 2 costs also remain credited. The remaining lower-bound, total-cost, provenance, uncertainty, and interpretation suggestions are distinct from those closed objections. The current overall recommendation is 3/5 (Findings), soundness rises to 3.5/5, and reproducibility remains 3/5.
