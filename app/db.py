import os
import sqlite3
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    idx INTEGER PRIMARY KEY,
    timestamp REAL,
    agent_id TEXT,
    tool_name TEXT,
    decision TEXT,
    risk_score REAL,
    details TEXT,
    prev_hash TEXT,
    hash TEXT
);
CREATE TABLE IF NOT EXISTS approvals (
    request_id TEXT PRIMARY KEY,
    fingerprint TEXT,
    agent_id TEXT,
    tool_name TEXT,
    arguments TEXT,
    risk_score REAL,
    created_at REAL,
    status TEXT,
    approver TEXT
);
"""


@contextmanager
def db():
    """Opens the database, commits on success, always closes."""
    path = os.environ.get("BANKGUARD_DB", "bankguard.db")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()