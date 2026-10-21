"""Synthetic eval cases: the LLM writes the email, our code writes the expected answer."""

import difflib
import json
import random
import textwrap
from datetime import date
from pathlib import Path
from typing import Callable, NamedTuple

from drafter import llm
from drafter.context import ORDERS, warranty_facts

random.seed(3)
TODAY = "2026-10-21"
OUT_OF_WARRANTY = ["expired", "ended", "no longer", "out of warranty",
                   "not under warranty", "not covered"]
STYLES = {"polite": "polite and short",
          "hinglish": "Hinglish (Hindi words written in English letters)",
          "angry": "angry, with a few words in CAPITALS",
          "typos": "very short, with typos and no punctuation",
          "long": "long and rambling, with background details",
          "formal": "formal Indian English (Dear Sir/Madam, Kindly...)"}
PROBLEMS = ["it is making a loud noise", "the water pressure is low", "it keeps tripping",
            "water is leaking from it", "it does not start in the morning"]


def warranty(o: dict) -> dict:
    return warranty_facts(o, date.fromisoformat(TODAY))


class Scenario(NamedTuple):
    fits: Callable[[dict], bool]        # which orders this scenario can use
    situation: str                      # what the customer wants
    category: list[str]                 # the right answers...
    needs_human: bool
    facts: Callable[[dict], list]       # ...and what a correct reply must contain


SCENARIOS = {
    "where_is_it": Scenario(lambda o: o["status"] == "dispatched",
                            "asks where their order is and when it will arrive",
                            ["order_status"], False,
                            lambda o: [[o["tracking"]], [o["courier"]]]),
    "when_dispatch": Scenario(lambda o: o["status"] == "awaiting dispatch",
                              "paid recently and asks when it will be dispatched",
                              ["order_status"], False, lambda o: [[o["expected_dispatch"]]]),
    "warranty_in": Scenario(lambda o: warranty(o).get("in_warranty") is True,
                            "says {problem} and asks if it is under warranty",
                            ["warranty", "technical"], False,
                            lambda o: [["visit", "technician"]]),
    "warranty_out": Scenario(lambda o: warranty(o).get("in_warranty") is False,
                             "says {problem} and asks if it is under warranty",
                             ["warranty", "technical"], False,
                             lambda o: [OUT_OF_WARRANTY + [warranty(o)["warranty_until"]]]),
    "cancel": Scenario(lambda o: o["status"] == "awaiting dispatch",
                       "wants to cancel the order and get a refund",
                       ["cancel_refund"], True, lambda o: []),
    "complaint": Scenario(lambda o: o["status"] == "dispatched",
                          "is upset that the order is taking too long and complains",
                          ["complaint", "order_status"], True, lambda o: [[o["tracking"]]]),
}


def write_email(order: dict, situation: str, style: str) -> dict:
    first = order["customer"].split()[0]
    prompt = (f"Write one realistic email from {first}, a customer of Vardhan Pumps in "
              f"India. Their order is {order['order_id']} ({order['item']}). In the email, "
              f"the customer {situation}. Mention the order number. Writing style: {style}. "
              "Do not include tracking numbers or dates. "
              'Return JSON: {"subject": "...", "body": "..."}')
    out = llm.chat([{"role": "user", "content": prompt}], temperature=0.9)
    return json.loads(out.text)


def reject_reason(order: dict, mail: dict, sc: Scenario, kept: list) -> str | None:
    body = mail.get("body", "")
    if order["order_id"][4:] not in body + mail.get("subject", ""):
        return "no order number"
    if any(f in body for group in sc.facts(order) for f in group if f.isdigit()):
        return "leaks the answer"
    if any(difflib.SequenceMatcher(None, body, k["email"]["body"]).ratio() > 0.8
           for k in kept):
        return "near duplicate"
    return None


def main(want: int = 30, max_tries: int = 45) -> None:
    kept, dropped, tries = [], {}, 0
    while len(kept) < want and tries < max_tries:
        name = list(SCENARIOS)[tries % len(SCENARIOS)]
        tries += 1
        sc = SCENARIOS[name]
        order = random.choice([o for o in ORDERS.values() if sc.fits(o)])
        style = random.choice(list(STYLES))
        situation = sc.situation.format(problem=random.choice(PROBLEMS))
        mail = write_email(order, situation, STYLES[style])
        if reason := reject_reason(order, mail, sc, kept):
            dropped[reason] = dropped.get(reason, 0) + 1
            continue
        sender = order["customer"].lower().replace(" ", ".") + "@gmail.com"
        kept.append({
            "id": f"s{len(kept) + 1:02d}", "source": "synthetic",
            "tags": [sc.category[0], name, style],
            "email": {"sender": sender, "subject": mail.get("subject", ""),
                      "body": mail.get("body", ""), "received": TODAY},
            "expected": {"category": sc.category, "needs_human": sc.needs_human,
                         "must_include": sc.facts(order),
                         "must_not_include": OUT_OF_WARRANTY if name == "warranty_in" else []},
            "reference": None})

    lines = [json.dumps(k, ensure_ascii=False) + "\n" for k in kept]
    Path("data/synthetic.jsonl").write_text("".join(lines))
    print(f"generated {tries}, kept {len(kept)}, dropped {sum(dropped.values())} {dropped}")
    for k in kept[:3]:
        print(f"\n[{k['id']}] {', '.join(k['tags'])}\n{textwrap.fill(k['email']['body'][:300], 100)}")


if __name__ == "__main__":
    main()
