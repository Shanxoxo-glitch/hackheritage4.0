"""
Dependency-free evaluator for a dumped LightGBM binary classifier.

The scoring API loads PyTorch and the voice model in the same process.
On macOS, importing LightGBM alongside PyTorch can cause OpenMP runtime
conflicts, so inference uses the dumped LightGBM trees directly.
"""

import math

import numpy as np


def _walk(node, x):
    while "leaf_value" not in node:
        v = x[node["split_feature"]]
        dt = node.get("decision_type", "<=")

        if dt == "<=":
            if math.isnan(v):
                left = bool(node.get("default_left", True))
            else:
                left = v <= node["threshold"]

        elif dt == "==":
            cats = {
                float(c)
                for c in str(node["threshold"]).split("||")
            }
            left = (
                not math.isnan(v)
                and v in cats
            )

        else:
            raise ValueError(
                f"unsupported decision_type {dt}"
            )

        node = (
            node["left_child"]
            if left
            else node["right_child"]
        )

    return node["leaf_value"]


def raw_score(dump, X):
    X = np.asarray(X, dtype=float)

    trees = dump["tree_info"]

    out = np.zeros(len(X))

    for i, x in enumerate(X):
        out[i] = sum(
            _walk(t["tree_structure"], x)
            for t in trees
        )

    return out


def predict_proba(dump, X):
    s = raw_score(dump, X)

    p1 = 1.0 / (1.0 + np.exp(-s))

    return np.stack(
        [1.0 - p1, p1],
        axis=1,
    )
