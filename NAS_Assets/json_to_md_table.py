#!/usr/bin/env python3
"""
Read eval results JSON and print a Markdown table sorted by avg_budget ascending.

Usage:
    python json_to_md_table.py <json_file>
    python json_to_md_table.py SINGLE_DOCUMENT_QA/top_configs/summary_20260617_203430.json
"""

import json
import sys


def json_to_md_table(json_path):
    with open(json_path) as f:
        data = json.load(f)

    # Sort by avg_budget ascending
    data.sort(key=lambda x: x["avg_budget"])

    # Discover all dataset names from the first entry
    dataset_names = []
    for entry in data:
        for ds in entry.get("dataset_scores", {}):
            if ds not in dataset_names:
                dataset_names.append(ds)

    # Build header
    cols = ["#", "Avg Budget", "Evicted Attn"] + dataset_names + ["Avg Score"]
    header = "| " + " | ".join(cols) + " |"
    separator = "| " + " | ".join(["---"] * len(cols)) + " |"

    # Build rows
    rows = []
    for i, entry in enumerate(data):
        avg_budget = f"{entry['avg_budget']:.0f}"
        evicted_attn = f"{entry['evicted_attn']:.3f}" if entry.get("evicted_attn") is not None else "N/A"
        ds_scores = []
        for ds in dataset_names:
            score = entry.get("dataset_scores", {}).get(ds)
            ds_scores.append(f"{score:.2f}" if score is not None else "-")
        avg_score = f"{entry['avg_score']:.2f}" if entry.get("avg_score") is not None else "-"

        row = [str(i), avg_budget, evicted_attn] + ds_scores + [avg_score]
        rows.append("| " + " | ".join(row) + " |")

    # Print table
    print(header)
    print(separator)
    for row in rows:
        print(row)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <json_file>")
        sys.exit(1)
    json_to_md_table(sys.argv[1])
