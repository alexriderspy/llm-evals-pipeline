"""Draft a reply to one email from the terminal: python -m drafter --case h12 --version v1"""

import argparse

from drafter import config
from drafter.drafter import build_messages, draft_reply
from evals.cases import load_cases

ap = argparse.ArgumentParser()
ap.add_argument("--case", required=True, help="an email from the golden set, e.g. h12")
ap.add_argument("--version", default=config.PROMPT_VERSION)
args = ap.parse_args()

email = next(c.email for c in load_cases() if c.id == args.case)
print(build_messages(email, args.version)[1]["content"], "\n")
completion, draft = draft_reply(email, args.version)
if draft is None:
    print("the model's output didn't match the schema:\n", completion.text)
else:
    print(f"category: {draft.category}   needs_human: {draft.needs_human}\n\n{draft.reply}\n")
cached = " (from cache)" if completion.cached else ""
print(f"{completion.tokens_in} tokens in, {completion.tokens_out} out, "
      f"{completion.latency_ms / 1000:.1f} s{cached}")
