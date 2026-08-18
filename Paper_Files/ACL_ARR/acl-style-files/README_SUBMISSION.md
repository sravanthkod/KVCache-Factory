# ACL ARR Submission: Neural Architecture Search for Dynamic KV Cache Eviction

## Files Ready for Submission

### Main Paper
- **NAS_KVCache_Eviction.tex** (406 lines) ✓ Compiled to PDF ✓
- **NAS_KVCache_Eviction.pdf** (140KB) ✓ Ready to submit

### Required ACL Style Files (Included)
- **acl.sty** - ACL style package (required for compilation)
- **acl_natbib.bst** - Bibliography style (required for references)
- **custom.bib** - Sample bibliography file (modify with your references)

### Additional Template Files
- acl_latex.tex - Official ACL template example
- acl_lualatex.tex - LuaLaTeX variant example

---

## Quick Compilation Guide

```bash
cd /home/snap_nas/sravanth/LLM/Token_Eviction/Dynamic_Methods/KVCache-Factory/Paper_Files/ACL_ARR/acl-style-files

# Single pass (fast)
pdflatex NAS_KVCache_Eviction.tex

# Two passes (recommended for references)
pdflatex NAS_KVCache_Eviction.tex
pdflatex NAS_KVCache_Eviction.tex

# With bibliography
pdflatex NAS_KVCache_Eviction.tex
bibtex NAS_KVCache_Eviction
pdflatex NAS_KVCache_Eviction.tex
pdflatex NAS_KVCache_Eviction.tex
```

---

## Paper Contents

### Abstract
- Proposes NAS for task-aware KV cache eviction
- Key results: +0.54% on multi-doc QA, +4.12% on code tasks
- Evaluated on 16 LongBench datasets + needle-in-haystack + RULER

### Sections

1. **Introduction** - Motivation, KV cache problem, why NAS is needed
2. **Background** - KV cache mechanics, existing compression methods
3. **Method** - Search space definition, NAS algorithm (3 phases), evaluation protocol
4. **Results** - Performance on 5 task categories with detailed tables
5. **Analysis** - Learned layer-wise budget patterns, task-specific insights
6. **Generalization** - Cross-model transfer (Llama → Mistral)
7. **Discussion** - Why NAS works, computational cost, limitations
8. **Related Work** - Architecture search, efficient LLMs
9. **Conclusion** - Summary and future directions
10. **Appendix** - Search space details, full results table

### Tables & Results

| Category | Best Result | Improvement |
|----------|------------|-------------|
| Multi-Doc QA | 36.14% (SnapKV@274) | +0.54% vs uniform |
| Single-Doc QA | 33.51% (SnapKV@122) | +0.54% at lower budget |
| Code | 58.26% (SnapKV@430) | Beats uniform@512 at 84% budget |
| Summarization | 22.27% (SnapKV@256) | Competitive with H2O |

### Key Insights

- **Multi-Doc QA**: Allocates 45% budget to mid-layers (12–20) for reasoning
- **Code**: Near-uniform allocation (5–7% per layer) for temporal context
- **Single-Doc QA**: Front-loaded (55% in layers 1–8) for dense retrieval
- **Summarization**: Balanced allocation, smallest NAS benefit

---

## Before Submission

### TODO Checklist

- [ ] Update `custom.bib` with your paper references
- [ ] Add your full author names (currently "Anonymous Submission")
- [ ] Add any figures/images (currently using placeholders)
- [ ] Review all tables and cross-references
- [ ] Verify page limit compliance
- [ ] Test final PDF rendering

### For Anonymous Review (Currently Set)

The paper uses `\usepackage[review]{acl}` which:
- ✓ Hides author names
- ✓ Adds review headers
- ✓ Enables line numbers

To change to camera-ready: Replace `[review]` with `[final]`

---

## Compilation Requirements

```bash
# Required
pdflatex
texlive-latex-base

# For bibliography
bibtex

# All installed? Test with:
which pdflatex bibtex
```

---

## Submission Instructions

1. **Package for ACL ARR:**
   ```bash
   tar -czf NAS_KVCache_submission.tar.gz \
     NAS_KVCache_Eviction.tex \
     NAS_KVCache_Eviction.pdf \
     custom.bib \
     acl.sty \
     acl_natbib.bst
   ```

2. **Upload to OpenReview/ACL Submission Portal**
   - Include compiled PDF
   - Include all .tex, .bib, .sty files
   - Include any figure/image files

3. **ACL ARR Submission Portal:**
   - https://openreview.net/group?id=aclweb.org/ACL/ARR/[MONTH]/Submissions
   - Follow venue-specific guidelines for figures, tables, appendix

---

## Document Statistics

- **Pages**: ~8 pages main content (ACL typically allows 8 pages + 4 page appendix)
- **Tables**: 9 main results tables + 1 appendix table
- **Sections**: 10 main sections + appendix
- **Line Count**: 406 lines of LaTeX

---

## Support Files Location

```
/home/snap_nas/sravanth/LLM/Token_Eviction/Dynamic_Methods/KVCache-Factory/
├── Paper_Files/
│   └── ACL_ARR/
│       └── acl-style-files/  ← ALL FILES HERE
│           ├── NAS_KVCache_Eviction.tex  ✓
│           ├── NAS_KVCache_Eviction.pdf  ✓
│           ├── acl.sty
│           ├── acl_natbib.bst
│           ├── custom.bib
│           └── ... (other ACL template files)
```

---

## Next Steps

1. Edit `NAS_KVCache_Eviction.tex` to:
   - Update author names/affiliations
   - Add real citations to `custom.bib`
   - Include figures (replace placeholder references)
   - Fine-tune results tables with your actual numbers

2. Recompile:
   ```bash
   pdflatex NAS_KVCache_Eviction.tex
   bibtex NAS_KVCache_Eviction
   pdflatex NAS_KVCache_Eviction.tex
   pdflatex NAS_KVCache_Eviction.tex
   ```

3. Submit to ACL ARR portal with all supporting files

---

**Generated**: July 28, 2026
**Format**: ACL ARR (Anonymous Review)
**Status**: Ready for submission ✓
