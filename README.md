# llm-evals-pipeline

An evaluation pipeline for a real LLM feature: a support-email reply drafter for Vardhan Pumps (a made-up pump company in Pune), running locally on `qwen2.5:7b` through Ollama.

It has a golden set in version control, four kinds of graders, a parallel runner with a cache and a SQLite results store, a regression comparison with bootstrap confidence intervals and per-slice breakdowns, a CI quality gate in GitHub Actions, and an HTML report with cost and latency.

## Quickstart

```bash
# 1. the model (one time)
ollama pull qwen2.5:7b

# 2. the project
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# 3. check the model answers, then run the tests for the graders (no LLM needed)
python -m scripts.check_setup
pytest -q

# 4. build the golden set and run the evals
python -m evals.build_golden
python -m evals.run --version v1
python -m evals.run --version v2           # add --judge to grade with the LLM judge too
python -m evals.compare v1 v2           # bootstrap CI, slices, fixed and broken cases
python -m evals.head_to_head v1 v2      # pairwise judge, both orders
python -m evals.judge_agreement         # can we trust the judge? vs 30 hand labels
python -m evals.reference_check v1 v2   # does embedding similarity track quality?
python -m evals.gate                    # exits 1 if quality drops
python -m evals.report v2               # writes reports/<run>.html
```

To use a cloud model instead, change three lines in `.env`: `LLM_BASE_URL`, `LLM_API_KEY` and `LLM_MODEL` (any OpenAI-compatible API). Set `PRICE_IN_PER_M` and `PRICE_OUT_PER_M` to your provider's prices to get real costs.

## Layout

```
drafter/                 the feature under test
  config.py              every setting, from env vars
  llm.py                 one chat() call with a cache, token counts and timing
  context.py             finds the order; v2 computes warranty dates and checks the sender
  guards.py              v2 removes lines that try to instruct the model
  drafter.py             prompt + order record -> Draft(category, needs_human, reply)
  prompts/v1.md, v2.md   the two prompt versions we compare
data/
  handbook.md            the support handbook: the spec the replies are graded against
  make_orders.py         40 realistic orders
  handwritten.jsonl      30 hand-written cases with reference replies
  make_synthetic.py      LLM writes the email, code writes the expected answer
evals/
  cases.py               the Case schema
  build_golden.py        merges, drops rejected cases -> golden.jsonl (56 cases)
  graders/checks.py      deterministic checks: schema, facts, invented numbers, policy
  graders/reference.py   embedding similarity to a reference reply
  graders/judge.py       LLM-as-judge: naive, rubric and claim-by-claim prompts
  graders/pairwise.py    A vs B, asked twice with the order swapped
  graders/prompts/       the judge rubric, the naive judge and the pairwise prompt
  judge_agreement.py     judge vs 30 hand labels: agreement and Cohen's kappa
  human_labels.jsonl     30 replies labelled pass/fail by hand
  reference_check.py     embedding similarity vs pass/fail
  head_to_head.py        pairwise win rate of two runs
  run.py                 parallel runner -> results.db
  compare.py             paired bootstrap, slices, fixed and broken cases
  gate.py                the CI gate (thresholds.json)
  report.py              HTML report (templates/report.html)
tests/                   unit tests for the graders and the statistics
scripts/                 check_setup.py and show_case.py
.github/workflows/evals.yml   tests, then smoke evals on Ollama, then the gate
```
