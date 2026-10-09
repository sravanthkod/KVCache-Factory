#!/usr/bin/env python3
"""Consolidate every AdaKV NAS result (LongBench + RULER) into ADAKV_RESULTS.md, figures/ and data/.

Run from anywhere:  /storage_data/sravanth/venvs/kv/bin/python3 ADAKV_RESULTS/generate_adakv_report.py
"""
import csv
import glob
import json
import os
from datetime import date

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "ADAKV_RESULTS")
FIG = os.path.join(OUT, "figures")
DATA = os.path.join(OUT, "data")
os.makedirs(FIG, exist_ok=True)
os.makedirs(DATA, exist_ok=True)

# ─── Palette (dataviz reference instance, light mode, fixed slot order) ──────
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3de"
NEUTRAL = "#9a9992"
S1, S2, S3, S4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
DIVERGING = LinearSegmentedColormap.from_list(
    "bluegrayred", ["#104281", "#3987e5", "#f0efec", "#e66767", "#a8201f"])
SEQ = LinearSegmentedColormap.from_list(
    "blue_seq", ["#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#0d366b"])

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "axes.titlecolor": INK, "axes.titleweight": "bold", "axes.titlesize": 11,
    "axes.titlelocation": "left", "font.size": 9.5, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "axes.axisbelow": True,
})

LB_CATS = ["SINGLE_DOCUMENT_QA", "MULTI_DOCUMENT_QA", "CODE", "SUMMARIZATION"]
SLICE_CATS = ["SINGLE_DOCUMENT_QA", "MULTI_DOCUMENT_QA", "CODE", "SUMMARIZATION"]
SLICE_BUDGETS = [128, 256, 512]
RULER_BUDGETS = [128, 256, 512, 1024, 1536, 2048]
ARCH_NAMES = {1: "Uniform", 2: "Winner (rescaled anchor)", 3: "Best heuristic", 4: "Best random", 5: "Best BO"}
ARCH_SHORT = {1: "Uniform", 2: "Winner", 3: "Heuristic", 4: "Random", 5: "BO"}
ARCH_COLORS = {2: S1, 3: S2, 4: S3, 5: S4}
ANCHORS = {"SINGLE_DOCUMENT_QA": "anchor_adakv_464.txt", "MULTI_DOCUMENT_QA": "anchor_adakv_188.txt",
           "CODE": "anchor_adakv_482.txt", "SUMMARIZATION": "anchor_adakv_548.txt", "RULER_ALL": "anchor_adakv_2536.txt"}
PRETTY = {"SINGLE_DOCUMENT_QA": "Single-Doc QA", "MULTI_DOCUMENT_QA": "Multi-Doc QA",
          "CODE": "Code", "SUMMARIZATION": "Summarization", "RULER_ALL": "RULER (all 11 tasks)"}

def p(*parts):
    return os.path.join(ROOT, *parts)


def fmt(x, nd=2):
    return f"{x:.{nd}f}"


def is_uniform(budgets):
    return len(set(budgets)) == 1


def pareto_mask(f1, f2):
    """Non-dominated rows for (minimize f1, minimize f2)."""
    n = len(f1)
    keep = np.ones(n, bool)
    for i in range(n):
        dom = (f1 <= f1[i]) & (f2 <= f2[i]) & ((f1 < f1[i]) | (f2 < f2[i]))
        if dom.any():
            keep[i] = False
    return keep


# ─── Loaders ─────────────────────────────────────────────────────────────────
def n_front(f1, sc, m):
    """Distinct objective points on the front (many x-vectors decode to the same discrete budgets)."""
    return len({(a, b) for a, b in zip(f1[m], sc[m])})


def load_step1(cat):
    d = np.loadtxt(p(cat, "adakv", "output.txt"))
    return d[:, -2], -d[:, -1]  # avg budget, calibration score


def load_step2(cat):
    """Full-benchmark eval of the Step-1 Pareto front -> list of dicts sorted by budget."""
    if cat == "CODE":
        # summary_20260904_174909.csv = the 13 original configs + the recovered avg_budget=482 config
        rows = []
        with open(p(cat, "adakv", "top_configs", "summary_20260904_174909.csv")) as f:
            for r in csv.DictReader(f):
                rows.append({
                    "avg_budget": float(r["avg_budget"]), "evicted_attn": float(r["evicted_attn"]),
                    "budgets": json.loads(r["budgets"]), "avg_score": float(r["avg_score"]),
                    "dataset_scores": {"lcc": float(r["lcc_score"]), "repobench-p": float(r["repobench-p_score"])},
                    "eval_time_sec": float(r["eval_time_sec"])})
        src = f"{cat}/adakv/top_configs/summary_20260904_174909.csv"
    else:
        files = sorted(glob.glob(p(cat, "adakv", "top_configs", "summary_*.json")))
        rows = json.load(open(files[-1]))
        src = os.path.relpath(files[-1], ROOT)
    rows.sort(key=lambda r: r["avg_budget"])
    return rows, src


def load_eval_csv(path):
    with open(path) as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        ds_cols = cols[cols.index("nas_f2") + 1: cols.index("mean_score")]
        rows = []
        for r in reader:
            rows.append({"arch": int(r["arch"]), "avg_budget": float(r["avg_budget"]),
                         "nas_f2": float(r["nas_f2"]), "scores": {c: float(r[c]) for c in ds_cols},
                         "mean": float(r["mean_score"]), "budgets": [int(x) for x in r["budgets"].split()]})
    return rows, ds_cols


def load_anchor(name):
    return [int(x) for x in open(p("anchors", name)).read().split()]


# ─── Collect ─────────────────────────────────────────────────────────────────
step1 = {c: load_step1(c) for c in LB_CATS}
step2 = {c: load_step2(c) for c in LB_CATS}
slices = {(c, b): load_eval_csv(p(f"{c}_B{b}", "adakv", "top_configs", "eval_results.csv"))
          for c in SLICE_CATS for b in SLICE_BUDGETS}
slice_rows = {(c, b): sum(1 for _ in open(p(f"{c}_B{b}", "adakv", "output.txt")))
              for c in SLICE_CATS for b in SLICE_BUDGETS}
ruler_step2, ruler_tasks = load_eval_csv(p("RULER_ALL", "adakv", "top_configs", "eval_results_total.csv"))
ruler_step2.sort(key=lambda r: r["avg_budget"])
ruler_slices = {b: load_eval_csv(p(f"RULER_ALL_B{b}", "adakv", "top_configs", "eval_results.csv"))[0]
                for b in RULER_BUDGETS}
ruler_slice_rows = {b: sum(1 for _ in open(p(f"RULER_ALL_B{b}", "adakv", "output.txt"))) for b in RULER_BUDGETS}
ruler_b64 = load_eval_csv(p("RULER_ALL_B64", "adakv", "top_configs", "eval_results.csv"))[0]
ruler_uniform64 = next(r for r in ruler_step2 if r["avg_budget"] == 64.0 and is_uniform(r["budgets"]))


def by_arch(rows):
    return {r["arch"]: r for r in rows}


# ─── Data dumps (flat CSVs for downstream use) ───────────────────────────────
with open(os.path.join(DATA, "longbench_step2_pareto_full_eval.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["category", "avg_budget", "type", "dataset", "score", "avg_score", "eval_time_sec", "budgets"])
    for c in LB_CATS:
        for r in step2[c][0]:
            for ds, s in r["dataset_scores"].items():
                w.writerow([c, r["avg_budget"], "uniform" if is_uniform(r["budgets"]) else "shaped", ds, s,
                            r["avg_score"], round(r.get("eval_time_sec", 0), 1), " ".join(map(str, r["budgets"]))])

with open(os.path.join(DATA, "longbench_slices_step3_4.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["category", "target_budget", "arch", "arch_name", "dataset", "score", "mean_score", "gain_vs_uniform", "budgets"])
    for (c, b), (rows, ds_cols) in slices.items():
        u = by_arch(rows)[1]["mean"]
        for r in rows:
            for ds in ds_cols:
                w.writerow([c, b, r["arch"], ARCH_NAMES[r["arch"]], ds, r["scores"][ds], round(r["mean"], 3),
                            round(r["mean"] - u, 3), " ".join(map(str, r["budgets"]))])

with open(os.path.join(DATA, "ruler_all_results.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["stage", "target_budget", "arch", "arch_name", "avg_budget"] + ruler_tasks + ["mean_score", "budgets"])
    for r in ruler_step2:
        w.writerow(["step2_pareto_full500", "", r["arch"], "uniform" if is_uniform(r["budgets"]) else "shaped",
                    r["avg_budget"]] + [r["scores"][t] for t in ruler_tasks] + [round(r["mean"], 3), " ".join(map(str, r["budgets"]))])
    for r in ruler_b64:
        w.writerow(["step3_fixed_budget", 64, r["arch"], "Winner (rescaled anchor)", r["avg_budget"]]
                   + [r["scores"][t] for t in ruler_tasks] + [round(r["mean"], 3), " ".join(map(str, r["budgets"]))])
    for b in RULER_BUDGETS:
        for r in ruler_slices[b]:
            w.writerow(["step3_4_slice", b, r["arch"], ARCH_NAMES[r["arch"]], r["avg_budget"]]
                       + [r["scores"][t] for t in ruler_tasks] + [round(r["mean"], 3), " ".join(map(str, r["budgets"]))])


# ─── Figures ─────────────────────────────────────────────────────────────────
def log2_axis(ax, ticks):
    ax.set_xscale("log", base=2)
    ax.set_xticks(ticks)
    ax.set_xticklabels([str(t) for t in ticks])
    ax.minorticks_off()


def save(fig, name):
    fig.savefig(os.path.join(FIG, name), dpi=160, bbox_inches="tight")
    plt.close(fig)


# Fig 1 — Step-1 search archives
# Background "evaluated config" scatter is subsampled for readability (fixed seed, so it's
# reproducible across re-runs); the Pareto front itself is always the full, unsampled front.
FIG1_SCATTER_CAP = 180
_rng = np.random.default_rng(0)

fig, axes = plt.subplots(2, 2, figsize=(11, 7.6))
for ax, c in zip(axes.flat, LB_CATS):
    f1, sc = step1[c]
    m = pareto_mask(f1, -sc)
    bg_idx = np.where(~m)[0]
    if len(bg_idx) > FIG1_SCATTER_CAP:
        bg_idx = _rng.choice(bg_idx, size=FIG1_SCATTER_CAP, replace=False)
    ax.scatter(f1[bg_idx], sc[bg_idx], s=14, color=NEUTRAL, alpha=0.55, linewidths=0,
               label=f"Evaluated config ({len(bg_idx)})")
    order = np.argsort(f1[m])
    ax.plot(f1[m][order], sc[m][order], color=S1, lw=2, marker="o", ms=6, mec=SURFACE, mew=1.5,
            label=f"Pareto front ({n_front(f1, sc, m)})")
    log2_axis(ax, [64, 128, 256, 512, 1024] + ([2048, 4096] if f1.max() > 1024 else []))
    ax.set_title(PRETTY.get(c, c.title()))
    ax.set_xlabel("Average per-layer KV budget (tokens)")
    ax.set_ylabel("Calibration score (30% sample)")
    ax.legend(loc="lower right", fontsize=8.5)
fig.suptitle("Step 1: unconstrained NAS search archives (AdaKV, Llama-3-8B-Instruct)", x=0.01, ha="left",
             fontweight="bold", fontsize=12.5)
fig.tight_layout()
save(fig, "fig1_step1_search_archives.png")

# Fig 2 — Step-2 full-benchmark Pareto
fig, axes = plt.subplots(2, 2, figsize=(11, 7.6))
for ax, c in zip(axes.flat, LB_CATS):
    rows = step2[c][0]
    uni = [r for r in rows if is_uniform(r["budgets"])]
    shp = [r for r in rows if not is_uniform(r["budgets"])]
    ax.plot([r["avg_budget"] for r in uni], [r["avg_score"] for r in uni], color=NEUTRAL, lw=2, marker="s",
            ms=6, mec=SURFACE, mew=1.5, label="Uniform budget (all layers equal)")
    ax.scatter([r["avg_budget"] for r in shp], [r["avg_score"] for r in shp], s=46, color=S1,
               edgecolors=SURFACE, linewidths=1.5, zorder=3, label="Per-layer shaped (NAS)")
    best = max(shp, key=lambda r: r["avg_score"]) if shp else None
    if best:
        ax.annotate(f"{best['avg_score']:.2f} @ {best['avg_budget']:.0f}", (best["avg_budget"], best["avg_score"]),
                    xytext=(0, 10), textcoords="offset points", ha="center", fontsize=8.5, color=INK2,
                    bbox=dict(boxstyle="round,pad=0.2", fc=SURFACE, ec="none"))
    mx = max(r["avg_budget"] for r in rows)
    log2_axis(ax, [64, 128, 256, 512, 1024] + ([2048, 4096] if mx > 1024 else []))
    ax.set_title(PRETTY.get(c, c.title()))
    ax.set_xlabel("Average per-layer KV budget (tokens)")
    ax.set_ylabel("Full-benchmark score")
    ax.legend(loc="lower right", fontsize=8.5)
fig.suptitle("Step 2: Pareto-front configs re-evaluated on the full LongBench data", x=0.01, ha="left",
             fontweight="bold", fontsize=12.5)
fig.tight_layout()
save(fig, "fig2_step2_pareto_full_eval.png")


def gain_bars(ax, groups, get_rows, title):
    width = 0.19
    x = np.arange(len(groups))
    for k, arch in enumerate([2, 3, 4, 5]):
        vals = []
        for g in groups:
            ba = by_arch(get_rows(g))
            vals.append(ba[arch]["mean"] - ba[1]["mean"] if arch in ba else np.nan)
        pos = x + (k - 1.5) * width
        ax.bar(pos, vals, width, color=ARCH_COLORS[arch], edgecolor=SURFACE, linewidth=1.2, label=ARCH_SHORT[arch])
    ax.axhline(0, color=INK2, lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels([f"B{g}" for g in groups])
    ax.set_title(title)
    ax.set_ylabel("Mean score gain vs uniform (points)")
    ax.grid(axis="x", visible=False)


# Fig 3 — LongBench slices
fig, axes = plt.subplots(1, 4, figsize=(17, 4.3), sharey=True)
for ax, c in zip(axes, SLICE_CATS):
    gain_bars(ax, SLICE_BUDGETS, lambda b, c=c: slices[(c, b)][0], PRETTY[c])
for ax in axes[1:]:
    ax.set_ylabel("")
fig.suptitle("Steps 3+4: fixed-budget slices, each architecture's gain over the uniform baseline (LongBench)",
             x=0.01, ha="left", fontweight="bold", fontsize=12.5)
fig.tight_layout(rect=(0, 0, 1, 0.93))
fig.legend(*axes[0].get_legend_handles_labels(), loc="upper right", ncol=4, fontsize=9, bbox_to_anchor=(0.995, 0.965))
save(fig, "fig3_longbench_slices_gain_vs_uniform.png")

# Fig 4 — RULER Step-2 Pareto
fig, ax = plt.subplots(figsize=(7.5, 4.6))
uni = [r for r in ruler_step2 if is_uniform(r["budgets"])]
shp = [r for r in ruler_step2 if not is_uniform(r["budgets"])]
ax.plot([r["avg_budget"] for r in uni], [r["mean"] for r in uni], color=NEUTRAL, lw=2, marker="s", ms=6,
        mec=SURFACE, mew=1.5, label="Uniform budget")
ax.scatter([r["avg_budget"] for r in shp], [r["mean"] for r in shp], s=46, color=S1, edgecolors=SURFACE,
           linewidths=1.5, zorder=3, label="Per-layer shaped (NAS)")
log2_axis(ax, [64, 128, 256, 512, 1024, 2048, 4096])
ax.set_xlabel("Average per-layer KV budget (tokens)")
ax.set_ylabel("Mean score, 11 RULER tasks (full 500)")
ax.set_title("RULER Step 2: Pareto front, full-500 evaluation")
ax.legend(loc="lower right", fontsize=8.5)
fig.tight_layout()
save(fig, "fig4_ruler_step2_pareto.png")

# Fig 5 — RULER slices
fig, ax = plt.subplots(figsize=(10, 4.4))
gain_bars(ax, RULER_BUDGETS, lambda b: ruler_slices[b], "RULER Steps 3+4: gain over uniform at each fixed budget")
fig.tight_layout(rect=(0, 0, 1, 0.92))
fig.legend(*ax.get_legend_handles_labels(), loc="upper right", ncol=4, fontsize=9, bbox_to_anchor=(0.995, 0.99))
save(fig, "fig5_ruler_slices_gain_vs_uniform.png")

# Fig 6 — RULER per-task gain of the best arch vs uniform
mat = np.zeros((len(ruler_tasks), len(RULER_BUDGETS)))
best_arch = {}
for j, b in enumerate(RULER_BUDGETS):
    ba = by_arch(ruler_slices[b])
    best = max((a for a in ba if a != 1), key=lambda a: ba[a]["mean"])
    best_arch[b] = best
    for i, t in enumerate(ruler_tasks):
        mat[i, j] = ba[best]["scores"][t] - ba[1]["scores"][t]
lim = max(1.0, np.abs(mat).max())
fig, ax = plt.subplots(figsize=(8, 6))
im = ax.imshow(mat, cmap=DIVERGING, norm=TwoSlopeNorm(0, -lim, lim), aspect="auto")
for i in range(mat.shape[0]):
    for j in range(mat.shape[1]):
        v = mat[i, j]
        ax.text(j, i, f"{v:+.1f}", ha="center", va="center", fontsize=8,
                color="#ffffff" if abs(v) > 0.6 * lim else INK)
ax.set_xticks(range(len(RULER_BUDGETS)))
ax.set_xticklabels([f"B{b}" for b in RULER_BUDGETS])
ax.set_yticks(range(len(ruler_tasks)))
ax.set_yticklabels(ruler_tasks)
ax.grid(False)
ax.set_title("RULER: per-task gain of the best NAS architecture over uniform (points)")
cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
cb.outline.set_visible(False)
fig.tight_layout()
save(fig, "fig6_ruler_per_task_gain_heatmap.png")

# Fig 6b — LongBench per-dataset gain of the best arch vs uniform (same idea as fig 6)
lb_rows, lb_cat_breaks = [], []
for c in SLICE_CATS:
    ds_cols = slices[(c, SLICE_BUDGETS[0])][1]
    for ds in ds_cols:
        lb_rows.append((c, ds))
    lb_cat_breaks.append(len(lb_rows))
mat = np.zeros((len(lb_rows), len(SLICE_BUDGETS)))
for j, b in enumerate(SLICE_BUDGETS):
    for i, (c, ds) in enumerate(lb_rows):
        ba = by_arch(slices[(c, b)][0])
        best = max((a for a in ba if a != 1), key=lambda a: ba[a]["mean"])
        mat[i, j] = ba[best]["scores"][ds] - ba[1]["scores"][ds]
lim = max(1.0, np.abs(mat).max())
fig, ax = plt.subplots(figsize=(6.5, 0.38 * len(lb_rows) + 1.4))
im = ax.imshow(mat, cmap=DIVERGING, norm=TwoSlopeNorm(0, -lim, lim), aspect="auto")
for i in range(mat.shape[0]):
    for j in range(mat.shape[1]):
        v = mat[i, j]
        ax.text(j, i, f"{v:+.1f}", ha="center", va="center", fontsize=8,
                color="#ffffff" if abs(v) > 0.6 * lim else INK)
ax.set_xticks(range(len(SLICE_BUDGETS)))
ax.set_xticklabels([f"B{b}" for b in SLICE_BUDGETS])
ax.set_yticks(range(len(lb_rows)))
ax.set_yticklabels([f"{PRETTY[c]}: {ds}" for c, ds in lb_rows], fontsize=8.5)
ax.grid(False)
for brk in lb_cat_breaks[:-1]:
    ax.axhline(brk - 0.5, color=SURFACE, lw=3)
ax.set_title("LongBench: per-dataset gain of the best NAS architecture over uniform (points)")
cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
cb.outline.set_visible(False)
fig.tight_layout()
save(fig, "fig6b_longbench_per_task_gain_heatmap.png")

# Fig 7 — per-layer allocation shapes (best arch per slice + anchors), log2(budget / mean)
labels, shapes = [], []
for c in SLICE_CATS:
    a = load_anchor(ANCHORS[c])
    labels.append(f"{PRETTY[c]}: anchor ({ANCHORS[c].split('_')[-1][:-4]})")
    shapes.append(a)
    for b in SLICE_BUDGETS:
        ba = by_arch(slices[(c, b)][0])
        best = max((k for k in ba if k != 1), key=lambda k: ba[k]["mean"])
        labels.append(f"{PRETTY[c]} B{b}: {ARCH_SHORT[best]}")
        shapes.append(ba[best]["budgets"])
a = load_anchor(ANCHORS["RULER_ALL"])
labels.append("RULER: anchor (2536)")
shapes.append(a)
for b in RULER_BUDGETS:
    ba = by_arch(ruler_slices[b])
    labels.append(f"RULER B{b}: {ARCH_SHORT[best_arch[b]]}")
    shapes.append(ba[best_arch[b]]["budgets"])
rel = np.array([np.log2(np.array(s) / np.mean(s)) for s in shapes])
lim = np.abs(rel).max()
fig, ax = plt.subplots(figsize=(12, 0.34 * len(labels) + 1.6))
im = ax.imshow(rel, cmap=DIVERGING, norm=TwoSlopeNorm(0, -lim, lim), aspect="auto")
ax.set_yticks(range(len(labels)))
ax.set_yticklabels(labels, fontsize=8.5)
ax.set_xticks(range(0, 32, 2))
ax.set_xlabel("Layer index")
ax.grid(False)
for y in [4, 8, 12]:
    ax.axhline(y - 0.5, color=SURFACE, lw=3)
ax.set_title("Per-layer allocation of the best architecture per slice: log2(layer budget / mean budget)")
cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.01)
cb.set_label("red = above mean, blue = below mean", color=INK2)
cb.outline.set_visible(False)
fig.tight_layout()
save(fig, "fig7_per_layer_allocation_shapes.png")


# ─── Markdown ────────────────────────────────────────────────────────────────
L = []
A = L.append
A("# AdaKV: complete NAS results (LongBench + RULER)")
A("")
A(f"_Generated {date.today().isoformat()} by `ADAKV_RESULTS/generate_adakv_report.py` from the raw result files; "
  "re-run the script to refresh. Model: Meta-Llama-3-8B-Instruct (32 layers). Eviction method: AdaKV._")
A("")
A("## Contents")
A("1. [Pipeline and status](#1-pipeline-and-status)")
A("2. [LongBench Step 1: search archives](#2-longbench-step-1-unconstrained-search-archives)")
A("3. [LongBench Step 2: Pareto front on full data](#3-longbench-step-2-pareto-front-re-evaluated-on-full-data)")
A("4. [LongBench Steps 3+4: fixed-budget slices](#4-longbench-steps-34-fixed-budget-slices)")
A("5. [RULER results](#5-ruler-results)")
A("6. [Per-layer allocation shapes](#6-per-layer-allocation-shapes)")
A("7. [Caveats and data-quality notes](#7-caveats-and-data-quality-notes)")
A("8. [Source files](#8-source-files)")
A("")
A("## 1. Pipeline and status")
A("")
A("| Step | What it does | Output |")
A("|---|---|---|")
A("| 1 | Unconstrained multi-objective NAS (LAMP), minimise avg budget and maximise calibration score (30% sample) | `<CAT>/adakv/output.txt` |")
A("| 2 | Re-evaluate every Pareto-optimal config on the full benchmark; extract the best shaped config as the **winner anchor** | `<CAT>/adakv/top_configs/summary_*.json`, `anchors/anchor_adakv_<budget>.txt` |")
A("| 3 | Rescale the winner anchor to fixed mean budgets (128/256/512...) and compare with uniform | arch 1 vs arch 2 in the slice tables |")
A("| 4 | Budget-constrained NAS at each fixed mean budget, then full-eval 5 architectures: Uniform, Winner, best Heuristic, best Random, best BO | `<CAT>_B<T>/adakv/top_configs/eval_results.csv` |")
A("")
A("| Benchmark / category | Step 1 | Step 2 | Steps 3+4 |")
A("|---|---|---|---|")
for c in LB_CATS:
    n1 = len(step1[c][0])
    n2 = len(step2[c][0])
    s34 = ", ".join(f"B{b} ({slice_rows[(c, b)]} search rows)" for b in SLICE_BUDGETS) if c in SLICE_CATS else "Not started"
    A(f"| LongBench {PRETTY[c]} | Done, {n1} configs | Done, {n2} Pareto configs | {s34} |")
A(f"| RULER (11 tasks) | Done, 100 configs (`../NAS_Assets/RULER_ALL_4096/`) | Done, {len(ruler_step2)} Pareto configs | B64 (Step 3 only), "
  + ", ".join(f"B{b} ({ruler_slice_rows[b]})" for b in RULER_BUDGETS) + " |")
A("")

A("## 2. LongBench Step 1: unconstrained search archives")
A("")
A("![Step 1 archives](figures/fig1_step1_search_archives.png)")
A("")
A("| Category | Datasets | Configs evaluated | Pareto-optimal (distinct) | Per-layer budget grid | Best calibration score |")
A("|---|---|---|---|---|---|")
for c in LB_CATS:
    f1, sc = step1[c]
    m = pareto_mask(f1, -sc)
    grid = "{64..4096} (7 options)" if f1.max() > 1024 else "{64..1024} (5 options)"
    dsn = ", ".join(step2[c][0][0]["dataset_scores"].keys())
    A(f"| {PRETTY[c]} | {dsn} | {len(f1)} | {n_front(f1, sc, m)} | {grid} | {sc.max():.2f} |")
A("")

A("## 3. LongBench Step 2: Pareto front re-evaluated on full data")
A("")
A("![Step 2 Pareto](figures/fig2_step2_pareto_full_eval.png)")
A("")
for c in LB_CATS:
    rows, src = step2[c]
    ds = list(rows[0]["dataset_scores"].keys())
    A(f"### {PRETTY[c]}")
    A(f"_Source: `{src}`_")
    A("")
    A("| # | Avg budget | Type | " + " | ".join(ds) + " | **Avg score** | Eval time (h) |")
    A("|---|---|---|" + "---|" * len(ds) + "---|---|")
    uni_scores = {r["avg_budget"]: r["avg_score"] for r in rows if is_uniform(r["budgets"])}
    for i, r in enumerate(rows):
        t = "uniform" if is_uniform(r["budgets"]) else "shaped"
        flag = " (from log)" if r.get("recovered_from_log") else ""
        A(f"| {i} | {r['avg_budget']:.0f} | {t}{flag} | " + " | ".join(fmt(r["dataset_scores"][d]) for d in ds)
          + f" | **{fmt(r['avg_score'])}** | {r.get('eval_time_sec', 0) / 3600:.2f} |")
    shp = [r for r in rows if not is_uniform(r["budgets"])]
    if shp:
        best = max(shp, key=lambda r: r["avg_score"])
        # best shaped vs the nearest uniform at or above its budget
        above = [b for b in uni_scores if b >= best["avg_budget"]]
        cmp = ""
        if above:
            ub = min(above)
            cmp = f"; the uniform config at {ub:.0f} scores {uni_scores[ub]:.2f}"
        A("")
        A(f"Best shaped config: **{best['avg_score']:.2f} at avg budget {best['avg_budget']:.0f}**{cmp}.")
    if c in ANCHORS:
        A(f"Winner anchor extracted for Steps 3+4: `anchors/{ANCHORS[c]}` = `{' '.join(map(str, load_anchor(ANCHORS[c])))}`")
    A("")

A("## 4. LongBench Steps 3+4: fixed-budget slices")
A("")
A("Architectures: **1 Uniform** (all layers = target), **2 Winner** (Step-2 anchor rescaled to the target, i.e. Step 3), "
  "**3 Best heuristic** (best hand-designed shape: ramps/triangles/alternating), **4 Best random**, **5 Best BO** "
  "(best config found by the budget-constrained search). Every architecture has exactly the same mean budget.")
A("")
A("![Slices](figures/fig3_longbench_slices_gain_vs_uniform.png)")
A("")
A("### Summary: mean score per architecture")
A("")
A("| Category | Budget | Search rows | Uniform | Winner | Heuristic | Random | BO | Best | Gain vs uniform |")
A("|---|---|---|---|---|---|---|---|---|---|")
for c in SLICE_CATS:
    for b in SLICE_BUDGETS:
        ba = by_arch(slices[(c, b)][0])
        best = max(ba, key=lambda a: ba[a]["mean"])
        cells = [f"**{fmt(ba[a]['mean'])}**" if a == best else fmt(ba[a]["mean"]) for a in range(1, 6)]
        A(f"| {PRETTY[c]} | {b} | {slice_rows[(c, b)]} | " + " | ".join(cells)
          + f" | {ARCH_SHORT[best]} | {ba[best]['mean'] - ba[1]['mean']:+.2f} |")
A("")
A("![LongBench per-dataset gain](figures/fig6b_longbench_per_task_gain_heatmap.png)")
A("")
A("### Per-dataset detail")
for c in SLICE_CATS:
    for b in SLICE_BUDGETS:
        rows, ds_cols = slices[(c, b)]
        A("")
        A(f"**{PRETTY[c]}, B{b}**  (`{c}_B{b}/adakv/top_configs/eval_results.csv`)")
        A("")
        A("| Arch | " + " | ".join(ds_cols) + " | Mean | Per-layer budgets |")
        A("|---|" + "---|" * len(ds_cols) + "---|---|")
        for r in rows:
            A(f"| {ARCH_NAMES[r['arch']]} | " + " | ".join(fmt(r["scores"][d]) for d in ds_cols)
              + f" | {fmt(r['mean'])} | `{' '.join(map(str, r['budgets']))}` |")
A("")

A("## 5. RULER results")
A("")
A("### Step 2: Pareto front (full 500 samples per task)")
A("")
A("![RULER Pareto](figures/fig4_ruler_step2_pareto.png)")
A("")
A("| Arch | Avg budget | Type | " + " | ".join(ruler_tasks) + " | **Mean** |")
A("|---|---|---|" + "---|" * len(ruler_tasks) + "---|")
for r in ruler_step2:
    A(f"| {r['arch']} | {r['avg_budget']:.0f} | {'uniform' if is_uniform(r['budgets']) else 'shaped'} | "
      + " | ".join(fmt(r["scores"][t], 1) for t in ruler_tasks) + f" | **{fmt(r['mean'])}** |")
A("")
A(f"Winner anchor: `anchors/{ANCHORS['RULER_ALL']}` = `{' '.join(map(str, load_anchor(ANCHORS['RULER_ALL'])))}`")
A("")
A("### Steps 3+4: fixed-budget slices")
A("")
A("![RULER slices](figures/fig5_ruler_slices_gain_vs_uniform.png)")
A("")
A("| Budget | Search rows | Uniform | Winner | Heuristic | Random | BO | Best | Gain vs uniform |")
A("|---|---|---|---|---|---|---|---|---|")
w64 = ruler_b64[0]
A(f"| 64 | n/a (Step 3 only) | {fmt(ruler_uniform64['mean'])} (Step 2) | **{fmt(w64['mean'])}** | n/a | n/a | n/a | Winner | "
  f"{w64['mean'] - ruler_uniform64['mean']:+.2f} |")
for b in RULER_BUDGETS:
    ba = by_arch(ruler_slices[b])
    best = max(ba, key=lambda a: ba[a]["mean"])
    cells = [f"**{fmt(ba[a]['mean'])}**" if a == best else fmt(ba[a]["mean"]) for a in range(1, 6)]
    A(f"| {b} | {ruler_slice_rows[b]} | " + " | ".join(cells)
      + f" | {ARCH_SHORT[best]} | {ba[best]['mean'] - ba[1]['mean']:+.2f} |")
A("")
A("![RULER per-task](figures/fig6_ruler_per_task_gain_heatmap.png)")
A("")
A("### Per-task detail")
for b in [64] + RULER_BUDGETS:
    rows = ruler_b64 if b == 64 else ruler_slices[b]
    A("")
    A(f"**RULER B{b}**  (`RULER_ALL_B{b}/adakv/top_configs/eval_results.csv`)")
    A("")
    A("| Arch | " + " | ".join(ruler_tasks) + " | Mean | Per-layer budgets |")
    A("|---|" + "---|" * len(ruler_tasks) + "---|---|")
    for r in rows:
        name = "Winner (rescaled anchor)" if b == 64 else ARCH_NAMES[r["arch"]]
        A(f"| {name} | " + " | ".join(fmt(r["scores"][t], 1) for t in ruler_tasks)
          + f" | {fmt(r['mean'])} | `{' '.join(map(str, r['budgets']))}` |")
A("")

A("## 6. Per-layer allocation shapes")
A("")
A("Each row is the best architecture in a slice (or a winner anchor), shown as log2(layer budget / mean budget): "
  "red layers get more than the mean, blue layers less, grey is exactly the mean.")
A("")
A("![Allocation shapes](figures/fig7_per_layer_allocation_shapes.png)")
A("")

A("## 7. Caveats and data-quality notes")
A("")
A("- **LongBench vs RULER search spaces.** LongBench Step 1 used per-layer budgets {64..1024}; RULER Step 1 used {64..4096}.")
A("- **Summarization Step 1 was rerun.** Its original run searched per-layer budgets up to 4096 instead of 1024 (the space "
  "used by the other three LongBench categories); the results here are from a corrected rerun on the {64..1024} grid, "
  "matching the others. The original 4096-grid archive was kept for reference (`SUMMARIZATION/adakv_old/`), not deleted.")
A("- **Code Step 1 is partial (149 configs).** Its Step-2 table uses `summary_20260904_174909.csv`, which adds the "
  "recovered avg_budget=482 config (the Code winner anchor).")
A("- **Minimum per-layer budget.** All LongBench slices and RULER B128/B256/B512 used a floor of 64. "
  "RULER B1024, B1536 and B2048 searched with a floor of 16 (launched before `run_ruler_lamp.py` switched 16 to 64), "
  "and RULER B64 (winner rescale only) used 16.")
A("- **Search budgets vary.** Most slice searches were accepted at 100-360 rows rather than the nominal 1000 "
  "(only Multi-Doc QA B256 reached 1000) because of repeated crashes caused by other jobs on the shared GPUs.")
A("- **Scores are rounded as stored.** Differences under ~0.3 points between architectures are within run-to-run noise "
  "and should not be over-interpreted.")
A("")

A("## 8. Source files")
A("")
A("| What | Path (relative to `NAS_Assets_SNAP_NAS/`) |")
A("|---|---|")
A("| Step-1 archives | `<CAT>/adakv/output.txt` |")
A("| Step-2 summaries | `<CAT>/adakv/top_configs/summary_*.json` / `.csv` |")
A("| Winner anchors | `anchors/anchor_adakv_{464,188,482,548,2536}.txt` |")
A("| LongBench slices | `<CAT>_B{128,256,512}/adakv/top_configs/eval_results.csv` |")
A("| RULER Step 2 | `RULER_ALL/adakv/top_configs/eval_results_total.csv` |")
A("| RULER slices | `RULER_ALL_B{64,128,256,512,1024,1536,2048}/adakv/top_configs/eval_results.csv` |")
A("| Slice run log / incidents | `LONGBENCH_STEP4_QUEUE.md`, `RULER_NAS_RUNBOOK.md` |")
A("| Flat CSV exports (this folder) | `ADAKV_RESULTS/data/*.csv` |")
A("")

with open(os.path.join(OUT, "ADAKV_RESULTS.md"), "w") as f:
    f.write("\n".join(L))
print("Wrote", os.path.join(OUT, "ADAKV_RESULTS.md"))
print("Figures:", sorted(os.listdir(FIG)))
print("Data:", sorted(os.listdir(DATA)))
