"""Pairwise evaluation of two runs: for each email, which version's reply wins?"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from drafter import config
from evals import store
from evals.cases import load_cases
from evals.compare import resolve
from evals.graders.pairwise import compare


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("new")
    args = ap.parse_args()
    ids = [resolve(args.base), resolve(args.new)]
    a = {r["case_id"]: r["reply"] for r in store.load_results(ids[0])}
    b = {r["case_id"]: r["reply"] for r in store.load_results(ids[1])}
    cases = [c for c in load_cases() if c.id in a and c.id in b]

    with ThreadPoolExecutor(max_workers=config.EVAL_CONCURRENCY) as pool:
        outcomes = list(pool.map(lambda c: compare(c.email, a[c.id], b[c.id]), cases))
    n = Counter(outcomes)
    print(f"{ids[0]} vs {ids[1]}: {len(cases)} emails, each judged twice, A and B swapped\n")
    print(f"  {args.new} wins       {n['2']:>3}")
    print(f"  {args.base} wins       {n['1']:>3}")
    print(f"  tie            {n['tie']:>3}")
    print(f"  inconsistent   {n['inconsistent']:>3}   (the verdict flipped with the order)")
    decided = n["1"] + n["2"]
    if decided:
        print(f"\n{args.new} wins {n['2']}/{decided} = {n['2'] / decided:.0%} "
              "of the emails where the judge was consistent")


if __name__ == "__main__":
    main()
