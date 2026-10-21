"""Compare two runs: the overall change with a confidence interval, then by slice and case."""

import argparse
from collections import defaultdict

from evals import store
from evals.metrics import CHECKS
from evals.stats import paired_bootstrap


def resolve(run: str) -> str:
    """Accept a run id, or a version name meaning its latest full run."""
    return run if "-" in run else store.latest_run(run)


def line(name: str, base: list[float], new: list[float]) -> None:
    diff, low, high = paired_bootstrap(base, new)
    star = "  *" if low > 0 or high < 0 else ""
    rates = f"{sum(base) / len(base):7.1%}{sum(new) / len(new):8.1%}"
    print(f"{name:<18}{rates}{diff * 100:+9.1f} pts  "
          f"[{low * 100:+.1f}, {high * 100:+.1f}]{star}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("base", help="run id or version, e.g. v1")
    ap.add_argument("new", help="run id or version, e.g. v2")
    args = ap.parse_args()
    ids = [resolve(args.base), resolve(args.new)]
    a = {r["case_id"]: r for r in store.load_results(ids[0])}
    b = {r["case_id"]: r for r in store.load_results(ids[1])}
    common = sorted(a.keys() & b.keys())
    print(f"{ids[0]}  vs  {ids[1]}   ({len(common)} cases)\n")

    print(f"{'':<18}{'base':>7}{'new':>8}{'change':>13}   95% CI")
    line("pass rate", [a[c]["passed"] for c in common], [b[c]["passed"] for c in common])
    for check in CHECKS:
        line(f"  {check}", [a[c]["checks"].get(check, False) for c in common],
             [b[c]["checks"].get(check, False) for c in common])
    print("* = the interval doesn't include zero\n")

    slices = defaultdict(list)
    for c in common:
        for tag in a[c]["tags"]:
            slices[tag].append(c)
    print(f"{'slice':<18}{'n':>3}{'base':>8}{'new':>8}")
    for tag, cs in sorted(slices.items(), key=lambda kv: -len(kv[1])):
        if len(cs) >= 3:  # smaller slices are too noisy to read anything into
            pa, pb = (sum(r[c]["passed"] for c in cs) / len(cs) for r in (a, b))
            print(f"{tag:<18}{len(cs):>3}{pa:8.0%}{pb:8.0%}")

    fixed = [c for c in common if not a[c]["passed"] and b[c]["passed"]]
    broke = [c for c in common if a[c]["passed"] and not b[c]["passed"]]
    print(f"\nfixed ({len(fixed)}): {' '.join(fixed)}")
    print(f"broke ({len(broke)}): {' '.join(broke)}")


if __name__ == "__main__":
    main()
