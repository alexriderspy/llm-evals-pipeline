"""Prompt-injection filter: lines that try to instruct the bot never reach the model."""

import re

INJECTION_RE = re.compile(
    r"(ignore|disregard|forget)\s+(all\s+|your\s+|the\s+|any\s+|previous\s+|prior\s+)*"
    r"(rules|instructions)|note to the (ai|assistant|bot)|system prompt|you are now",
    re.IGNORECASE)


def strip_injection(body: str) -> tuple[str, bool]:
    """Remove suspicious lines. Returns the cleaned body and whether we removed any."""
    kept = [line for line in body.splitlines() if not INJECTION_RE.search(line)]
    removed = len(kept) < len(body.splitlines())
    if removed:
        kept.append("[A line that tried to give instructions to the assistant was removed.]")
    return "\n".join(kept), removed
