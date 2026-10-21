"""Pairwise comparison: show the judge two replies and ask which one is better."""

import json
from pathlib import Path

from drafter import config, llm
from drafter.drafter import HANDBOOK, Email
from evals.graders.judge import judge_context

PROMPT = (Path(__file__).parent / "prompts" / "pairwise.md").read_text()


def ask(email: Email, first: str, second: str) -> str:
    user = (f"{judge_context(email)}\n\n--- Reply A ---\n{first}\n\n"
            f"--- Reply B ---\n{second}")
    out = llm.chat([{"role": "system", "content": PROMPT.format(handbook=HANDBOOK)},
                    {"role": "user", "content": user}], model=config.JUDGE_MODEL)
    try:
        return json.loads(out.text).get("winner", "tie")
    except json.JSONDecodeError:
        return "tie"


def compare(email: Email, reply_1: str, reply_2: str) -> str:
    """Ask twice with the order swapped. Only a verdict that survives the swap counts."""
    a = ask(email, reply_1, reply_2)  # reply_1 shown as A
    b = ask(email, reply_2, reply_1)  # reply_1 shown as B
    if a == "A" and b == "B":
        return "1"
    if a == "B" and b == "A":
        return "2"
    return "tie" if a == b == "tie" else "inconsistent"
