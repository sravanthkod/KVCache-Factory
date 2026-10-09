#!/usr/bin/env python3
"""The budget decoder (continuous weights -> integer per-layer budgets) must hit the target mean exactly and respect
the floor and cap. Loaded from nas/run_longbench_lamp.py without importing its model dependencies.

    python tests/test_decoder.py"""
import ast
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "nas" / "run_longbench_lamp.py"
fn = next(n for n in ast.parse(SRC.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == "x_point_to_budgets_continuous")
ns = {"np": np}
exec(compile(ast.Module(body=[fn], type_ignores=[]), "decoder", "exec"), ns)
decode = ns["x_point_to_budgets_continuous"]

rng = np.random.default_rng(0)
n = 0
for floor in (16, 64):
    for B in (128, 256, 512, 1024, 2048):
        for _ in range(200):
            x = rng.random(32)
            b = np.array(decode(x, 32, B, floor, 4096))
            assert b.sum() == 32 * B, (floor, B, b.sum())
            assert b.min() >= floor and b.max() <= 4096, (floor, B, b.min(), b.max())
            n += 1
        b = np.array(decode(np.full(32, 0.5), 32, B, floor, 4096))  # a constant vector is the uniform allocation
        assert (b == B).all(), (floor, B, b)
print(f"decoder ok: {n} random vectors hit the target mean exactly within [floor, cap]; constant vectors decode to uniform")
