"""Turn a list of case results into the numbers we care about."""

import numpy as np

CHECKS = ["schema", "category", "needs_human", "facts", "forbidden",
          "grounded_numbers", "english", "signoff", "length"]


def summary(rows: list[dict]) -> dict:
    latency = np.array([r["latency_ms"] for r in rows])
    judged = [r["judge"] for r in rows if r.get("judge")]
    return {
        "cases": len(rows),
        "passed": int(sum(r["passed"] for r in rows)),
        "pass_rate": float(np.mean([r["passed"] for r in rows])),
        "checks": {c: float(np.mean([r["checks"].get(c, False) for r in rows]))
                   for c in CHECKS},
        "judge_pass_rate": float(np.mean([j["pass"] for j in judged])) if judged else None,
        "p50_ms": float(np.percentile(latency, 50)),
        "p95_ms": float(np.percentile(latency, 95)),
        "tokens_in": int(sum(r["tokens_in"] for r in rows)),
        "tokens_out": int(sum(r["tokens_out"] for r in rows)),
        "cost_usd": float(sum(r["cost_usd"] for r in rows)),
        "cached": int(sum(r["cached"] for r in rows)),
    }


def print_summary(s: dict) -> None:
    print(f"\npass rate        {s['pass_rate']:.1%}  "
          f"({s['passed']}/{s['cases']} cases pass every check)")
    for check, rate in s["checks"].items():
        print(f"  {check:<17}{rate:6.1%}")
    if s["judge_pass_rate"] is not None:
        print(f"judge pass rate  {s['judge_pass_rate']:.1%}")
    print(f"latency          p50 {s['p50_ms'] / 1000:.1f} s   "
          f"p95 {s['p95_ms'] / 1000:.1f} s")
    print(f"tokens           {s['tokens_in']:,} in   {s['tokens_out']:,} out   "
          f"cost ${s['cost_usd']:.4f}")
    print(f"cache hits       {s['cached']}/{s['cases']}")
