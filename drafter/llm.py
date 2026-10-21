"""One function to call the model, with a cache, token counts and timing."""

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass

from openai import APIConnectionError, APITimeoutError, InternalServerError, OpenAI

from drafter import config

client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)


@dataclass
class Completion:
    text: str
    tokens_in: int
    tokens_out: int
    latency_ms: float
    cached: bool = False

    @property
    def cost_usd(self) -> float:
        cost = self.tokens_in * config.PRICE_IN_PER_M + self.tokens_out * config.PRICE_OUT_PER_M
        return cost / 1e6


def _cache() -> sqlite3.Connection:
    db = sqlite3.connect(config.CACHE_PATH, timeout=30)
    db.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT)")
    return db


def chat(messages: list[dict], model: str = config.LLM_MODEL,
         temperature: float = 0.0) -> Completion:
    # Same model + same messages + same temperature = same answer, so we cache it.
    key = hashlib.sha256(json.dumps([model, messages, temperature]).encode()).hexdigest()
    with _cache() as db:
        row = db.execute("SELECT value FROM cache WHERE key = ?", (key,)).fetchone()
    if row:
        return Completion(**json.loads(row[0]), cached=True)

    start = time.perf_counter()
    for attempt in range(3):  # servers hiccup; retry twice, waiting 1 s then 2 s
        try:
            resp = client.chat.completions.create(
                model=model, messages=messages, temperature=temperature, seed=7,
                response_format={"type": "json_object"})  # JSON mode
            break
        except (APIConnectionError, APITimeoutError, InternalServerError):
            if attempt == 2:
                raise
            time.sleep(2**attempt)
    out = Completion(text=resp.choices[0].message.content or "",
                     tokens_in=resp.usage.prompt_tokens,
                     tokens_out=resp.usage.completion_tokens,
                     latency_ms=(time.perf_counter() - start) * 1000)
    with _cache() as db:
        value = {k: v for k, v in out.__dict__.items() if k != "cached"}
        db.execute("INSERT OR REPLACE INTO cache VALUES (?, ?)", (key, json.dumps(value)))
    return out
