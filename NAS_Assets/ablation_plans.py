"""
Plan and report three SnapKV/Llama LongBench ablations that reuse existing searches (no new
search; all scoring on this A100 so every number is comparable with the main tables):

  curve  Search-budget curve: best config (by calibration) among the first k rows of each
         Stage-4 search, k in {64, 96, 128, 160, 200, all}, scored on full data. k=64 is the
         initial design only (uniform + heuristics + winner seed + LHS points); k=all is the
         paper's "NAS-refined". Shows what the guided iterations add. Cells: CODE and
         SINGLE_DOCUMENT_QA x B128/256/512/1024.
  floor  Controlled floor ablation: the rescaled winner at per-layer floor 16 vs 64 (floor 64
         numbers already exist) for CODE / SINGLE_DOC / MULTI_DOC at B128 and B256.
  calib  Calibration-ratio study: ~24 configs of one cell (default CODE B512), calibration at
         10% (from the search's output.txt), 30% (new) vs full data -> Kendall tau, top-1 hit,
         regret per ratio.

  python3 ablation_plans.py <curve|floor|calib> plan     # writes ablations/<tag>/{plan,jobs}.json
  python3 eval_budget_jobs.py --jobs ablations/<tag>/jobs.json --out_dir ablations/<tag>   # GPU
  python3 ablation_plans.py <curve|floor|calib> report   # writes analysis_outputs/AB_<tag>.md

Run from NAS_Assets/ with PYTHONPATH=<repo root> and the cakekv python.
"""

import argparse
import csv
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_MD = os.path.join(os.path.dirname(HERE), "ICLR_Final_Results", "analysis_outputs")
CELLS = os.path.join(OUT_MD, "cells.csv")
ABL = os.path.join(HERE, "ablations")
METHOD, L = "snapkv", 32


def label_for(i):
    return "uniform" if i == 0 else "heuristic" if i <= 5 else "winner" if i == 6 else "random" if i <= 63 else "bo"


def parse_budgets(s):
    s = s.strip()
    v = json.loads(s) if s.startswith("[") else [int(x) for x in s.split()]
    return tuple(int(x) for x in v)


def known(cat, T):
    """tuple(budgets) -> (label, full_score, row_idx) for every full-data eval of this cell on disk."""
    out = {}
    for r in csv.DictReader(open(CELLS)):
        if r["benchmark"] == "longbench" and r["method"] == METHOD and r["category"] == cat and int(r["budget"]) == T:
            out[parse_budgets(r["budgets"])] = (r["label"], float(r["full_score"]), r["row_idx"])
    return out


def output_rows(cat, T):
    return np.loadtxt(os.path.join(HERE, f"{cat}_B{T}", METHOD, "output.txt"))


def decode_rows(rows, T):
    import run_longbench_lamp as rll
    rll.NAS_TARGET_BUDGET = T
    return [tuple(int(b) for b in rll._decode_budgets(np.asarray(r[:-2]), L)) for r in rows]


def save(tag, plan, jobs):
    d = os.path.join(ABL, tag)
    os.makedirs(d, exist_ok=True)
    json.dump(plan, open(os.path.join(d, "plan.json"), "w"), indent=1)
    json.dump(jobs, open(os.path.join(d, "jobs.json"), "w"), indent=1)
    print(f"-> {d}/plan.json, jobs.json: {len(jobs)} jobs")


def result(tag, name):
    p = os.path.join(ABL, tag, "results", name + ".json")
    return json.load(open(p))["mean_score"] if os.path.isfile(p) else None


def kendall(a, b):
    c = d = 0
    for i in range(len(a)):
        for j in range(i + 1, len(a)):
            s = (a[i] - a[j]) * (b[i] - b[j])
            c += s > 0
            d += s < 0
    return (c - d) / (c + d) if c + d else float("nan")


def write_md(name, lines):
    p = os.path.join(OUT_MD, name)
    open(p, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n-> {p}")


# ---------------------------------------------------------------- curve
CURVE_CATS, CURVE_BUDGETS, CURVE_KS = ["CODE", "SINGLE_DOCUMENT_QA"], [128, 256, 512, 1024], [64, 96, 128, 160, 200]


def plan_curve():
    plan, jobs, seen = [], [], set()
    for cat in CURVE_CATS:
        for T in CURVE_BUDGETS:
            rows, kn = output_rows(cat, T), known(cat, T)
            n = len(rows)
            bud = decode_rows(rows, T)
            for k in sorted({k for k in CURVE_KS if k < n} | {n}):
                i = int(np.argmin(rows[:k, -1]))
                b, hit = bud[i], kn.get(bud[i])
                e = dict(cat=cat, T=T, k=k, n_rows=n, row=i, label=label_for(i), calib=round(-float(rows[i, -1]), 4),
                         full_known=hit[1] if hit else None, job=None)
                if not hit:
                    e["job"] = f"curve_{cat}_B{T}_row{i}"
                    if e["job"] not in seen:
                        seen.add(e["job"])
                        jobs.append(dict(name=e["job"], category=f"{cat}", method=METHOD, budgets=list(b), sample_ratio=1.0))
                plan.append(e)
            uni = [v for v in kn.values() if v[0] == "uniform"]
            print(f"{cat} B{T}: {n} rows; " + " ".join(
                f"k={e['k']}->row{e['row']}({e['label']}){'*' if e['job'] else ''}" for e in plan if e["cat"] == cat and e["T"] == T)
                + (f" | uniform {uni[0][1]:.2f}" if uni else ""))
    print("(* = needs a new full-data eval)")
    save("search_budget_curve", plan, jobs)


def report_curve():
    tag = "search_budget_curve"
    plan = json.load(open(os.path.join(ABL, tag, "plan.json")))
    out = ["# Search-budget curve (SnapKV, Llama-3-8B-Instruct, full data, local A100)", "",
           "Best config by calibration among the first k rows of the Stage-4 search; k=64 is the initial design "
           "only, k=all is the paper's NAS-refined. Δ is vs the cell's uniform.", "",
           "| Cell | k | row (type) | calibration | full-data | Δ vs uniform |", "|---|---|---|---|---|---|"]
    by_k, missing = {}, 0
    for e in plan:
        full = e["full_known"] if e["full_known"] is not None else result(tag, e["job"])
        uni = [v[1] for v in known(e["cat"], e["T"]).values() if v[0] == "uniform"][0]
        if full is None:
            missing += 1
            out.append(f"| {e['cat']} B{e['T']} | {e['k']} | {e['row']} ({e['label']}) | {e['calib']:.2f} | (pending) | |")
            continue
        out.append(f"| {e['cat']} B{e['T']} | {e['k'] if e['k'] != e['n_rows'] else 'all (%d)' % e['n_rows']} | "
                   f"{e['row']} ({e['label']}) | {e['calib']:.2f} | {full:.2f} | {full - uni:+.2f} |")
        by_k.setdefault((e["cat"], e["T"]), {})[e["k"]] = full - uni
    out += ["", "**Mean Δ vs uniform by k (cells with a value at that k; k=all uses each cell's full length)**", "",
            "| k | mean Δ | cells |", "|---|---|---|"]
    for k in CURVE_KS + ["all"]:
        v = [d.get(k if k != "all" else max(d)) for d in by_k.values() if (k == "all" or k in d)]
        v = [x for x in v if x is not None]
        if v:
            out.append(f"| {k} | {np.mean(v):+.2f} | {len(v)} |")
    if missing:
        out.append(f"\n({missing} entries still pending GPU evals)")
    write_md("AB_search_budget_curve.md", out)


# ---------------------------------------------------------------- floor
FLOOR_CATS, FLOOR_BUDGETS = ["CODE", "SINGLE_DOCUMENT_QA", "MULTI_DOCUMENT_QA"], [128, 256]


def plan_floor():
    import run_longbench_lamp as rll
    plan, jobs = [], []
    for cat in FLOOR_CATS:
        a = np.loadtxt(os.path.join(HERE, "anchors", f"anchor_longbench_{cat}_{METHOD}.txt"))
        wx = 0.05 + 0.9 * (a / a.max())
        for T in FLOOR_BUDGETS:
            kn = known(cat, T)
            b64 = tuple(int(x) for x in rll.x_point_to_budgets_continuous(wx, L, T, 64, 4096))
            b16 = tuple(int(x) for x in rll.x_point_to_budgets_continuous(wx, L, T, 16, 4096))
            assert sum(b16) == sum(b64) == L * T, (cat, T)
            uni = [v[1] for v in kn.values() if v[0] == "uniform"][0]
            e = dict(cat=cat, T=T, uniform=uni, b64=list(b64), b16=list(b16), full64=kn.get(b64, (None, None))[1],
                     at_floor64=sum(x == 64 for x in b64), at_floor16=sum(x == 16 for x in b16),
                     job16=None if b16 == b64 else f"floor16_{cat}_B{T}",
                     job64=None if b64 in kn else f"floor64_{cat}_B{T}")
            for key, b in (("job16", b16), ("job64", b64)):
                if e[key]:
                    jobs.append(dict(name=e[key], category=cat, method=METHOD, budgets=list(b), sample_ratio=1.0))
            plan.append(e)
            print(f"{cat} B{T}: winner@64 known={e['full64']} layers@64={e['at_floor64']}, layers@16={e['at_floor16']}, "
                  f"floor16 job={'yes' if e['job16'] else 'no (identical)'}, floor64 job={'yes' if e['job64'] else 'no'}")
    save("floor", plan, jobs)


def report_floor():
    plan = json.load(open(os.path.join(ABL, "floor", "plan.json")))
    out = ["# Controlled floor ablation (SnapKV, same rescaled winner, floor 16 vs 64; full data)", "",
           "| Cell | uniform | winner, floor 64 | winner, floor 16 | Δ (16 - 64) | layers at floor (64 / 16 version) |",
           "|---|---|---|---|---|---|"]
    for e in plan:
        f64 = e["full64"] if e["full64"] is not None else result("floor", e["job64"]) if e["job64"] else None
        f16 = result("floor", e["job16"]) if e["job16"] else f64
        if f64 is None or f16 is None:
            out.append(f"| {e['cat']} B{e['T']} | {e['uniform']:.2f} | (pending) | (pending) | | |")
            continue
        out.append(f"| {e['cat']} B{e['T']} | {e['uniform']:.2f} | {f64:.2f} | {f16:.2f} | {f16 - f64:+.2f} | "
                   f"{e['at_floor64']} / {e['at_floor16']} |")
    write_md("AB_floor.md", out)


# ---------------------------------------------------------------- calib
def plan_calib(cat="CODE", T=512, n_total=24, seed=0):
    rows, kn = output_rows(cat, T), known(cat, T)
    bud = decode_rows(rows, T)
    chosen = {int(v[2]): b for b, v in kn.items() if v[2] != ""}
    rng = np.random.RandomState(seed)
    pools = [("heuristic", [i for i in range(1, 6)], 2), ("random", list(range(7, 64)), 8),
             ("bo", list(range(64, len(rows))), n_total - len(chosen) - 10)]
    for _, pool, want in pools:
        pool = [i for i in pool if i not in chosen and bud[i] not in chosen.values()]
        for i in rng.choice(pool, size=min(want, len(pool)), replace=False):
            chosen[int(i)] = bud[int(i)]
    plan, jobs = [], []
    for i in sorted(chosen):
        b = chosen[i]
        full = kn.get(b, (None, None))[1]
        e = dict(cat=cat, T=T, row=i, label=label_for(i), calib_0_1=round(-float(rows[i, -1]), 4), full_known=full,
                 job_full=None if full is not None else f"calib_{cat}_B{T}_row{i}_r1.0", job_0_3=f"calib_{cat}_B{T}_row{i}_r0.3")
        for key, ratio in (("job_full", 1.0), ("job_0_3", 0.3)):
            if e[key]:
                jobs.append(dict(name=e[key], category=cat, method=METHOD, budgets=list(b), sample_ratio=ratio))
        plan.append(e)
    # full-data jobs first (most informative), then the cheaper 30% ones
    jobs.sort(key=lambda j: j["sample_ratio"] != 1.0)
    print(f"{cat} B{T}: {len(plan)} configs (rows {[e['row'] for e in plan]}); "
          f"{sum(e['job_full'] is not None for e in plan)} new full-data evals, {len(plan)} new 30% evals")
    save("calibration_ratio", plan, jobs)


def report_calib():
    tag = "calibration_ratio"
    plan = json.load(open(os.path.join(ABL, tag, "plan.json")))
    rows = []
    for e in plan:
        full = e["full_known"] if e["full_known"] is not None else result(tag, e["job_full"])
        c3 = result(tag, e["job_0_3"])
        if full is not None and c3 is not None:
            rows.append((e, e["calib_0_1"], c3, full))
    out = [f"# Calibration-ratio study ({plan[0]['cat']} B{plan[0]['T']}, SnapKV; {len(rows)}/{len(plan)} configs complete)", "",
           "Calibration at 10% (from the search's own output.txt) and 30% vs full data for the same configs.", "",
           "| ratio | mean gap (calib - full) | Kendall tau vs full | calib-picked = full-best | regret |", "|---|---|---|---|---|"]
    if len(rows) >= 3:
        full = np.array([r[3] for r in rows])
        for name, idx in (("10%", 1), ("30%", 2)):
            cal = np.array([r[idx] for r in rows])
            out.append(f"| {name} | {np.mean(cal - full):+.2f} | {kendall(cal, full):+.2f} | "
                       f"{'yes' if np.argmax(cal) == np.argmax(full) else 'no'} | {full.max() - full[np.argmax(cal)]:.2f} |")
    out += ["", "| row (type) | calib 10% | calib 30% | full |", "|---|---|---|---|"]
    out += [f"| {e['row']} ({e['label']}) | {a:.2f} | {b:.2f} | {c:.2f} |" for e, a, b, c in rows]
    write_md("AB_calibration_ratio.md", out)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("which", choices=["curve", "floor", "calib"])
    p.add_argument("action", choices=["plan", "report"])
    a = p.parse_args()
    {("curve", "plan"): plan_curve, ("curve", "report"): report_curve, ("floor", "plan"): plan_floor,
     ("floor", "report"): report_floor, ("calib", "plan"): plan_calib, ("calib", "report"): report_calib}[(a.which, a.action)]()
