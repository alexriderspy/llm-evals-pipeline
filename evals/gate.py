"""The CI gate: exit with an error if the latest run is below the bar we agreed on."""

import argparse
import json
import sys
from pathlib import Path

from drafter import config
from evals import store
from evals.metrics import summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", default="full")
    ap.add_argument("--version", default=config.PROMPT_VERSION)
    args = ap.parse_args()
    bar = json.loads(Path("evals/thresholds.json").read_text())[args.suite]
    run_id = store.latest_run(args.version, args.suite)
    rows = store.load_results(run_id)
    s = summary(rows)
    print(f"gate for {run_id} ({len(rows)} cases)")

    p95, max_p95 = s["p95_ms"] / 1000, bar["max_p95_ms"] / 1000
    results = [
        (f"pass rate {s['pass_rate']:.1%} >= {bar['min_pass_rate']:.0%}",
         s["pass_rate"] >= bar["min_pass_rate"]),
        (f"p95 latency {p95:.1f} s <= {max_p95:.0f} s", p95 <= max_p95),
    ]
    if bar["min_judge_pass_rate"] is not None and s["judge_pass_rate"] is not None:
        results.append((f"judge pass rate {s['judge_pass_rate']:.1%} >= "
                        f"{bar['min_judge_pass_rate']:.0%}",
                        s["judge_pass_rate"] >= bar["min_judge_pass_rate"]))
    for r in rows:  # some cases must pass no matter what the average says
        critical = [t for t in r["tags"] if t in bar["must_pass_tags"]]
        if critical:
            results.append((f"{r['case_id']} ({critical[0]}) must always pass",
                            bool(r["passed"])))

    for text, ok in results:
        print(f"  {'ok  ' if ok else 'FAIL'}  {text}")
    if not all(ok for _, ok in results):
        print("quality gate FAILED")
        sys.exit(1)
    print("quality gate passed")


if __name__ == "__main__":
    main()
