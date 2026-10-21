"""A one-file HTML report for a run: the numbers, the slices, and every failing reply."""

import argparse
from collections import defaultdict
from html import escape
from pathlib import Path
from string import Template

from drafter import config
from evals import store
from evals.cases import load_cases
from evals.metrics import summary

TEMPLATE = Template((Path(__file__).parent / "templates" / "report.html").read_text())


def bar(v: float) -> str:
    return f'<div class="bar {"low" if v < 0.8 else ""}"><i style="width:{v:.0%}"></i></div>'


def card(value: str, label: str) -> str:
    return f'<div class="card"><b>{value}</b><span>{label}</span></div>'


def render(run_id: str) -> str:
    rows = store.load_results(run_id)
    s = summary(rows)
    judge = f"{s['judge_pass_rate']:.0%}" if s["judge_pass_rate"] is not None else "n/a"
    tokens = (s["tokens_in"] + s["tokens_out"]) / s["cases"]
    cards = [card(f"{s['pass_rate']:.0%}", f"pass every check ({s['passed']}/{s['cases']})"),
             card(judge, "judge pass rate"),
             card(f"{s['p50_ms'] / 1000:.1f} s", f"p50 latency, p95 {s['p95_ms'] / 1000:.1f} s"),
             card(f"{tokens:,.0f}", "tokens per email"),
             card(f"${s['cost_usd']:.2f}", "cost of this run")]
    checks = [f"<tr><td>{c}</td><td>{v:.0%}</td><td>{bar(v)}</td></tr>"
              for c, v in s["checks"].items()]

    by_tag = defaultdict(list)
    for r in rows:
        for t in r["tags"]:
            by_tag[t].append(r["passed"])
    rates = sorted((sum(v) / len(v), t, len(v)) for t, v in by_tag.items() if len(v) >= 3)
    slices = [f"<tr><td>{t}</td><td>{n}</td><td>{p:.0%}</td><td>{bar(p)}</td></tr>"
              for p, t, n in rates]

    emails = {c.id: c.email for c in load_cases()}
    fails = []
    for r in (r for r in rows if not r["passed"]):
        e = emails[r["case_id"]]
        failed = ", ".join(k for k, ok in r["checks"].items() if not ok)
        why = (r["judge"] or {}).get("reasoning", "")
        fails.append(f"<tr><td><b>{r['case_id']}</b><br>{', '.join(r['tags'])}</td>"
                     f"<td><b>{escape(e.subject)}</b><div class='small'>{escape(e.body[:220])}"
                     f"</div></td><td class='small'>{escape(r['reply'])}</td>"
                     f"<td class='fail'>{failed}</td><td class='small'>{escape(why)}</td></tr>")

    return TEMPLATE.substitute(run_id=run_id, cases=s["cases"], model=config.LLM_MODEL,
                               cards="".join(cards), checks="".join(checks),
                               slices="".join(slices), fails="".join(fails))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run", nargs="?", default=config.PROMPT_VERSION, help="run id or version")
    ap.add_argument("--suite", default="full")
    args = ap.parse_args()
    run_id = args.run if "-" in args.run else store.latest_run(args.run, args.suite)
    out = Path("reports") / f"{run_id}.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(render(run_id))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
