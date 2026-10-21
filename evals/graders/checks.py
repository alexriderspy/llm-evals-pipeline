"""Deterministic checks: plain Python, free, instant, and the same answer every time."""

import re
from datetime import date

from drafter.drafter import Draft
from evals.cases import Case

LONG_NUMBER_RE = re.compile(r"\b\d{5,}\b")  # tracking numbers, order numbers, serials
RUPEES_RE = re.compile(r"(?:Rs\.?|₹|INR)\s?(\d[\d,]*)", re.IGNORECASE)
PROMISE_RE = re.compile(r"refund (has been|will be) (processed|issued|credited)"
                        r"|claim (is|has been) approved|we will replace|has been cancelled",
                        re.IGNORECASE)
DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")


def date_patterns(iso: str) -> list[str]:
    """2026-10-23 can be written as 23 October, 23rd Oct, Oct 23, 23/10/2026..."""
    d = date.fromisoformat(iso)
    day, mon = rf"0?{d.day}(st|nd|rd|th)?", rf"{d.strftime('%b')}[a-z]*\.?"
    return [re.escape(iso), rf"\b{day}\s+(of\s+)?{mon}", rf"\b{mon}\s+{day}\b",
            rf"\b0?{d.day}[/-]0?{d.month}\b"]


def mentions(phrase: str, text: str) -> bool:
    if re.fullmatch(r"\d{4}-\d\d-\d\d", phrase):
        return any(re.search(p, text, re.IGNORECASE) for p in date_patterns(phrase))
    # whole words only, so "ended" doesn't match inside "extended"
    return re.search(rf"\b{re.escape(phrase)}\b", text, re.IGNORECASE) is not None


def grounded_numbers(reply: str, source: str) -> bool:
    """Every tracking number, order number and rupee amount must exist in the sources."""
    known = source.replace(",", "")
    rupees = [n.replace(",", "").rstrip(",") for n in RUPEES_RE.findall(reply)]
    return all(n in known for n in LONG_NUMBER_RE.findall(reply) + rupees)


def run_checks(case: Case, draft: Draft | None, source: str) -> dict[str, bool]:
    if draft is None:
        return {"schema": False}
    exp, reply = case.expected, draft.reply
    has_facts = all(any(mentions(p, reply) for p in group) for group in exp.must_include)
    forbidden = any(mentions(p, reply) for p in exp.must_not_include)
    return {
        "schema": True,
        "category": draft.category in exp.category,
        "needs_human": exp.needs_human is None or draft.needs_human == exp.needs_human,
        "facts": has_facts,
        "forbidden": not forbidden and not PROMISE_RE.search(reply),
        "grounded_numbers": grounded_numbers(reply, source),
        "english": not DEVANAGARI_RE.search(reply),
        "signoff": "Team Vardhan Pumps" in reply,
        "length": len(reply.split()) <= 150,
    }
