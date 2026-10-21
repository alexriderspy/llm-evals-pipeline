"""Can we trust the judge? Grade replies a person labelled, and measure the agreement."""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from drafter import config
from evals.cases import load_cases
from evals.graders.judge import judge
from evals.stats import cohen_kappa

LABELS = Path("evals/human_labels.jsonl")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rubric", default="v3", help="v1 'is it good?', v2 rubric, v3 claims")
    args = ap.parse_args()
    labels = [json.loads(line) for line in LABELS.read_text().splitlines() if line]
    cases = {c.id: c for c in load_cases()}

    def grade(label: dict) -> dict:
        return judge(cases[label["case_id"]].email, label["reply"], rubric=args.rubric)

    with ThreadPoolExecutor(max_workers=config.EVAL_CONCURRENCY) as pool:
        verdicts = list(pool.map(grade, labels))
    human = [label["human_pass"] for label in labels]
    model = [v["pass"] for v in verdicts]

    def count(h: bool, m: bool) -> int:
        return sum(1 for x, y in zip(human, model) if x == h and y == m)

    print(f"judge rubric {args.rubric}, {len(labels)} hand-labelled replies\n")
    print(f"{'':<14}{'judge pass':>11}{'judge fail':>12}")
    print(f"{'human pass':<14}{count(True, True):>11}{count(True, False):>12}")
    print(f"{'human fail':<14}{count(False, True):>11}{count(False, False):>12}")
    agree = sum(h == m for h, m in zip(human, model))
    print(f"\nagreement {agree}/{len(labels)} = {agree / len(labels):.0%}   "
          f"Cohen's kappa {cohen_kappa(human, model):.2f}")
    print("\ndisagreements:")
    for label, v in zip(labels, verdicts):
        if label["human_pass"] != v["pass"]:
            print(f"  {label['case_id']} ({label['version']})  "
                  f"human {'pass' if label['human_pass'] else 'fail'}, judge "
                  f"{'pass' if v['pass'] else 'fail'}: {v.get('reasoning', '')[:110]}")


if __name__ == "__main__":
    main()
