"""What one eval case looks like, and how to load the golden set."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from drafter.drafter import Email

GOLDEN = Path("evals/golden.jsonl")


class Expected(BaseModel):
    category: list[str]               # any of these is acceptable
    needs_human: bool | None          # None means either is fine
    must_include: list[list[str]] = []  # every group must match, any phrase in a group
    must_not_include: list[str] = []


class Case(BaseModel):
    id: str
    source: Literal["handwritten", "synthetic"]
    tags: list[str]
    email: Email
    expected: Expected
    reference: str | None = None      # a reply a good support agent would send


def load_cases(suite: str = "full") -> list[Case]:
    lines = GOLDEN.read_text().splitlines()
    cases = [Case.model_validate_json(line) for line in lines if line.strip()]
    return [c for c in cases if suite == "full" or suite in c.tags]
