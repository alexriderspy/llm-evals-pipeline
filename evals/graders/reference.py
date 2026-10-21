"""Reference-based scoring: how close is the reply to the one a good agent wrote?"""

import logging
from functools import lru_cache

logging.getLogger("torch.distributed.elastic.multiprocessing.redirects").setLevel(logging.ERROR)
from sentence_transformers import SentenceTransformer  # noqa: E402


@lru_cache(maxsize=1)
def model() -> SentenceTransformer:
    return SentenceTransformer("BAAI/bge-small-en-v1.5")  # 33M parameters, runs on a CPU


def similarity(replies: list[str], references: list[str]) -> list[float]:
    """Cosine similarity between each reply and its reference: 1 means same meaning."""
    a = model().encode(replies, normalize_embeddings=True)
    b = model().encode(references, normalize_embeddings=True)
    return [float(x @ y) for x, y in zip(a, b)]
