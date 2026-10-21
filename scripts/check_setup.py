"""Check that the model answers before we build anything on top of it."""

from drafter import config, llm

out = llm.chat([{"role": "user", "content": 'Reply with JSON: {"status": "ready"}'}])
print(f"model    {config.LLM_MODEL} at {config.LLM_BASE_URL}")
print(f"answer   {out.text.strip()}")
print(f"tokens   {out.tokens_in} in, {out.tokens_out} out")
print(f"latency  {out.latency_ms / 1000:.1f} s")
