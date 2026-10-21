"""Does similarity to a reference reply tell good replies from bad ones? Let's measure it."""

import argparse

import numpy as np

from evals import store
from evals.cases import load_cases
from evals.compare import resolve
from evals.graders.reference import similarity


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+", help="run ids or versions, e.g. v1 v2")
    args = ap.parse_args()
    refs = {c.id: c.reference for c in load_cases() if c.reference}
    rows = [r | {"run": run} for run in args.runs for r in store.load_results(resolve(run))
            if r["case_id"] in refs]
    sims = similarity([r["reply"] for r in rows], [refs[r["case_id"]] for r in rows])

    good = [s for s, r in zip(sims, rows) if r["passed"]]
    bad = [s for s, r in zip(sims, rows) if not r["passed"]]
    print(f"{len(rows)} replies with a hand-written reference\n")
    print(f"mean similarity, replies that pass every check   {np.mean(good):.3f}  (n={len(good)})")
    print(f"mean similarity, replies that fail a check       {np.mean(bad):.3f}  (n={len(bad)})")
    # AUC: pick one good and one bad reply at random; how often does the good one score higher?
    auc = np.mean([g > b for g in good for b in bad])
    print(f"chance a good reply scores above a bad one (AUC) {auc:.2f}   (0.5 = coin flip)\n")

    # A wrong fact is the failure that matters most. Does similarity notice it?
    content = {"facts", "forbidden", "grounded_numbers"}
    wrong = [(s, r) for s, r in zip(sims, rows)
             if any(not r["checks"].get(c, True) for c in content)]
    print("replies with a wrong or missing fact, highest similarity first:")
    for s, r in sorted(wrong, key=lambda x: -x[0])[:4]:
        failed = ", ".join(c for c in content if not r["checks"].get(c, True))
        print(f"  {s:.3f}  {r['case_id']} ({r['run']})  failed: {failed}")

if __name__ == "__main__":
    main()
