"""LLM-as-judge: a second model call grades the reply against a written rubric."""

import json
from datetime import date
from pathlib import Path

from drafter import config, llm
from drafter.context import find_order, warranty_facts
from drafter.drafter import HANDBOOK, Email

PROMPTS = Path(__file__).parent / "prompts"
RUBRIC = (PROMPTS / "judge_rubric.md").read_text()  # v2: four questions, then a verdict
NAIVE = (PROMPTS / "judge_naive.md").read_text()  # v1: "is this a good reply?"
CLAIMS = (PROMPTS / "judge_claims.md").read_text()  # v3: check every claim, then the rules


def judge_context(email: Email) -> str:
    """The judge sees the whole truth: the original email and the full order record."""
    order = find_order(f"{email.subject} {email.body}")
    record = "No order number in the email."
    if order:
        record = json.dumps(order | warranty_facts(order, date.fromisoformat(email.received)))
    return (f"Customer email:\nFrom: {email.sender}\nSubject: {email.subject}\n\n"
            f"{email.body}\n\nOrder record from our database:\n{record}")


def judge(email: Email, reply: str, rubric: str = "v3") -> dict:
    if rubric == "v1":
        system = NAIVE.format()
    elif rubric == "v2":
        system = RUBRIC.format(handbook=HANDBOOK, today=email.received)
    else:
        system = CLAIMS.format(handbook=HANDBOOK, today=email.received)
    user = f"{judge_context(email)}\n\n--- Reply to grade ---\n{reply}"
    out = llm.chat([{"role": "system", "content": system},
                    {"role": "user", "content": user}], model=config.JUDGE_MODEL)
    try:
        verdict = json.loads(out.text)
    except json.JSONDecodeError:
        verdict = {"verdict": "fail", "reasoning": "judge returned invalid JSON"}
    if rubric == "v3":  # the verdict comes from our code, not from the judge's mood
        claims_ok = all(c.get("supported") is True for c in verdict.get("claims", []))
        verdict["pass"] = claims_ok and not verdict.get("broken_rules")
    else:
        verdict["pass"] = verdict.get("verdict") == "pass"
    return verdict
