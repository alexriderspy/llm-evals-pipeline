"""Every setting in one place, read from environment variables (or a .env file)."""

import os

from dotenv import load_dotenv

load_dotenv()

# Ollama speaks the OpenAI API, so a cloud model is just a different URL, key and model.
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "ollama")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", LLM_MODEL)

# Which version of the drafter runs in production. The CI gate tests this one.
PROMPT_VERSION = os.getenv("PROMPT_VERSION", "v2")

# Your provider's price in US dollars per million tokens. A local model costs 0.
PRICE_IN_PER_M = float(os.getenv("PRICE_IN_PER_M", "0"))
PRICE_OUT_PER_M = float(os.getenv("PRICE_OUT_PER_M", "0"))

EVAL_CONCURRENCY = int(os.getenv("EVAL_CONCURRENCY", "4"))
CACHE_PATH = os.getenv("CACHE_PATH", "llm_cache.db")
RESULTS_PATH = os.getenv("RESULTS_PATH", "results.db")
