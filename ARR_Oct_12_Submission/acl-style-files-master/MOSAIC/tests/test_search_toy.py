#!/usr/bin/env python3
"""End-to-end smoke test of the search loop (LAMP.py: non-dominated sorting, MLP classifier, differential evolution) on a
cheap synthetic objective, with no GPU and no model. The real objective (run_longbench_lamp.py / run_ruler_lamp.py)
is replaced by a stub that scores allocations in closed form.

    python tests/test_search_toy.py"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

NAS = Path(__file__).resolve().parents[1] / "nas"
STUB = '''import numpy as np
LEVELS = np.array([64, 128, 256, 512, 1024, 2048, 4096])
def get_objective_values(x):
    b = LEVELS[np.minimum((np.asarray(x) * 7).astype(int), 6)]
    w = np.linspace(0.2, 1.0, 32)  # toy: later layers matter more
    return float(b.mean()), -float((w * np.log2(b)).sum() / w.sum())  # f1 = average budget, f2 = -score (both minimised)
'''
with tempfile.TemporaryDirectory() as tmp:
    for f in ("LAMP.py", "ndsort.py", "HFF_mod.py"):
        shutil.copy(NAS / f, tmp)
    Path(tmp, "run_longbench_lamp.py").write_text(STUB)
    env = dict(os.environ, NAS_INIT_POINTS="16", NAS_EVAL_BUDGET="26", NAS_TASK_CATEGORY="TOY", NAS_METHOD="toy",
               CUDA_VISIBLE_DEVICES="", PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1")
    r = subprocess.run([sys.executable, "LAMP.py"], cwd=tmp, env=env, capture_output=True, text=True, timeout=900)
    assert r.returncode == 0, r.stderr[-2000:]
    d = np.loadtxt(Path(tmp, "TOY", "toy", "output.txt"))
    assert d.shape == (26, 34), d.shape  # 32 layer weights + average budget + score
    assert d[:, -2].min() == 64 and d[:, -2].max() >= 1024
print("search loop ok: 26 evaluations (16 initial + 10 guided), 34 columns each, uniform anchors first")
