"""Merge the handwritten and synthetic cases into one golden set, check it, mark smoke."""

import json
from collections import Counter
from pathlib import Path

from evals.cases import GOLDEN, Case

# I read every synthetic email before it went in. These didn't pass the review.
REJECTED = {"s06": "garbled Hinglish, no real customer writes like this",
            "s07": "template placeholder left in: [Your Company Name]",
            "s12": "placeholder left in, and a product that doesn't exist (VS-2200)",
            "s16": "garbled Hinglish"}
# A small, fast subset for CI: the main categories plus the cases that must never fail.
SMOKE = ["h01", "h02", "h04", "h05", "h07", "h08", "h09", "h12", "h20", "h28",
         "s01", "s04"]


def main() -> None:
    lines = (Path("data/handwritten.jsonl").read_text().splitlines()
             + Path("data/synthetic.jsonl").read_text().splitlines())
    cases = [Case.model_validate_json(line) for line in lines]  # fails loudly if bad
    cases = [c for c in cases if c.id not in REJECTED]
    assert len({c.id for c in cases}) == len(cases), "duplicate case ids"
    for c in cases:
        if c.id in SMOKE:
            c.tags.append("smoke")
    GOLDEN.write_text("".join(json.dumps(c.model_dump(), ensure_ascii=False) + "\n"
                              for c in cases))

    print(f"{len(cases)} cases -> {GOLDEN}   (rejected in review: {', '.join(REJECTED)})")
    print("source:     ", dict(Counter(c.source for c in cases)))
    print("category:   ", dict(Counter(c.expected.category[0] for c in cases)))
    print("needs_human:", dict(Counter(str(c.expected.needs_human) for c in cases)))
    print("tags:       ", dict(Counter(t for c in cases for t in c.tags[1:]).most_common(12)))


if __name__ == "__main__":
    main()
