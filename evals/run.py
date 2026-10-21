"""Run the golden set through one version of the drafter, grade it, store the results."""

import argparse
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from drafter import config
from drafter.drafter import HANDBOOK, build_messages, draft_reply
from evals import store
from evals.cases import Case, load_cases
from evals.graders.checks import run_checks
from evals.graders.judge import judge
from evals.metrics import print_summary, summary


def evaluate_case(case: Case, version: str, with_judge: bool) -> dict:
    row = {"case_id": case.id, "tags": case.tags, "latency_ms": 0.0, "tokens_in": 0,
           "tokens_out": 0, "cost_usd": 0.0, "cached": False}
    email_and_context = build_messages(case.email, version)[1]["content"]
    try:
        completion, draft = draft_reply(case.email, version)
    except Exception as e:  # one broken case shouldn't kill a 56-case run
        return row | {"reply": f"ERROR: {e}", "checks": {"schema": False}, "passed": False}

    checks = run_checks(case, draft, source=email_and_context + HANDBOOK)
    row |= {"reply": draft.reply if draft else completion.text,
            "category": draft.category if draft else None,
            "needs_human": draft.needs_human if draft else None,
            "checks": checks, "passed": all(checks.values()),
            "latency_ms": completion.latency_ms, "tokens_in": completion.tokens_in,
            "tokens_out": completion.tokens_out, "cost_usd": completion.cost_usd,
            "cached": completion.cached}
    if with_judge and draft:
        row["judge"] = judge(case.email, draft.reply)
    return row


def status(row: dict) -> str:
    if row["reply"].startswith("ERROR"):
        return "FAIL " + row["reply"][:60]
    failed = [name for name, ok in row["checks"].items() if not ok]
    text = "pass" if row["passed"] else "FAIL " + ", ".join(failed)
    if row.get("judge"):
        text = f"judge {'pass' if row['judge']['pass'] else 'FAIL'}   checks {text}"
    return text


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default=config.PROMPT_VERSION)
    ap.add_argument("--suite", default="full", help="full, or a tag like smoke")
    ap.add_argument("--judge", action="store_true", help="also grade with the LLM judge")
    args = ap.parse_args()

    cases = load_cases(args.suite)
    git = ["git", "rev-parse", "--short", "HEAD"]
    sha = subprocess.run(git, capture_output=True, text=True).stdout.strip() or "local"
    run_id = store.new_run(args.version, args.suite, sha, len(cases))
    print(f"run {run_id}: {len(cases)} cases, model {config.LLM_MODEL}, "
          f"{config.EVAL_CONCURRENCY} in parallel")

    start, rows = time.perf_counter(), []
    grade = partial(evaluate_case, version=args.version, with_judge=args.judge)
    with ThreadPoolExecutor(max_workers=config.EVAL_CONCURRENCY) as pool:
        for i, row in enumerate(pool.map(grade, cases), 1):
            store.save_result(run_id, row)
            rows.append(row)
            secs = row["latency_ms"] / 1000
            print(f"[{i:2d}/{len(cases)}] {row['case_id']}  {secs:5.1f} s  {status(row)}")

    print_summary(summary(rows))
    print(f"wall time        {time.perf_counter() - start:.1f} s")
    print(f"saved as {run_id}")


if __name__ == "__main__":
    main()
