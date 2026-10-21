"""The results store: every run and every result goes into SQLite, to compare runs later."""

import json
import sqlite3
from datetime import datetime

from drafter import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY, created_at TEXT, version TEXT, model TEXT,
    suite TEXT, git_sha TEXT, n_cases INTEGER);
CREATE TABLE IF NOT EXISTS results (
    run_id TEXT, case_id TEXT, tags TEXT, reply TEXT, category TEXT,
    needs_human INTEGER, checks TEXT, passed INTEGER, judge TEXT, latency_ms REAL,
    tokens_in INTEGER, tokens_out INTEGER, cost_usd REAL, cached INTEGER,
    PRIMARY KEY (run_id, case_id));
"""
COLUMNS = ["case_id", "tags", "reply", "category", "needs_human", "checks", "passed",
           "judge", "latency_ms", "tokens_in", "tokens_out", "cost_usd", "cached"]
JSON_COLUMNS = ["tags", "checks", "judge"]


def connect() -> sqlite3.Connection:
    db = sqlite3.connect(config.RESULTS_PATH)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db


def new_run(version: str, suite: str, git_sha: str, n_cases: int) -> str:
    now = datetime.now()
    run_id = f"{version}-{now:%Y%m%d-%H%M%S}"
    with connect() as db:
        db.execute("INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (run_id, now.isoformat(timespec="seconds"), version,
                    config.LLM_MODEL, suite, git_sha, n_cases))
    return run_id


def save_result(run_id: str, row: dict) -> None:
    values = [json.dumps(row.get(c)) if c in JSON_COLUMNS else row.get(c) for c in COLUMNS]
    with connect() as db:
        db.execute(f"INSERT OR REPLACE INTO results VALUES (?{', ?' * len(COLUMNS)})",
                   [run_id, *values])


def load_results(run_id: str) -> list[dict]:
    with connect() as db:
        rows = db.execute("SELECT * FROM results WHERE run_id = ? ORDER BY case_id",
                          (run_id,)).fetchall()
    return [{k: json.loads(r[k]) if k in JSON_COLUMNS else r[k] for k in r.keys()}
            for r in rows]


def latest_run(version: str, suite: str = "full") -> str:
    """The newest complete run. A run that crashed halfway must never become the baseline."""
    with connect() as db:
        row = db.execute("""SELECT run_id FROM runs WHERE version = ? AND suite = ?
                            AND n_cases = (SELECT COUNT(*) FROM results r
                                           WHERE r.run_id = runs.run_id)
                            ORDER BY created_at DESC LIMIT 1""", (version, suite)).fetchone()
    if row is None:
        raise SystemExit(f"no {suite} run for {version} yet")
    return row["run_id"]
