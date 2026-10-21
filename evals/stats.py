"""Is the difference between two runs real, or noise? A paired bootstrap tells us."""

import numpy as np


def paired_bootstrap(a: list[float], b: list[float], n: int = 10_000,
                     seed: int = 0) -> tuple[float, float, float]:
    """a and b: per-case scores (1 = pass) on the same cases. Returns (b - a, low, high)."""
    a_, b_ = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    rng = np.random.default_rng(seed)
    # resample the cases with replacement, the same cases for both runs
    idx = rng.integers(0, len(a_), size=(n, len(a_)))
    diffs = b_[idx].mean(axis=1) - a_[idx].mean(axis=1)
    low, high = np.percentile(diffs, [2.5, 97.5])
    return float(b_.mean() - a_.mean()), float(low), float(high)


def cohen_kappa(x: list[bool], y: list[bool]) -> float:
    """Agreement between two raters, corrected for the agreement you'd get by chance."""
    x_, y_ = np.asarray(x, dtype=bool), np.asarray(y, dtype=bool)
    observed = np.mean(x_ == y_)
    chance = np.mean(x_) * np.mean(y_) + np.mean(~x_) * np.mean(~y_)
    return float((observed - chance) / (1 - chance)) if chance < 1 else 1.0
