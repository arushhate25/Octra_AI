import hashlib
import json
import time

from app.db import db

def _hash_entry(entry_body):
    payload = json.dumps(entry_body, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()

def _row_to_entry(row):
    return {
        "index": row["idx"],
        "timestamp": row["timestamp"],
        "agent_id": row["agent_id"],
        "tool_name": row["tool_name"],
        "decision": row["decision"],
        "risk_score": row["risk_score"],
        "details": json.loads(row["details"]),
        "prev_hash": row["prev_hash"],
        "hash": row["hash"],
    }

def log_event(agent_id, tool_name, decision, risk_score=None, details=None):
    with db() as conn:
        # Lock the database so two requests can't both extend the same chain link.
        conn.execute("BEGIN IMMEDIATE")
        last = conn.execute(
            "SELECT idx, hash FROM audit_log ORDER BY idx DESC LIMIT 1"
        ).fetchone()
        entry = {
            "index": last["idx"] + 1 if last else 0,
            "timestamp": time.time(),
            "agent_id": agent_id,
            "tool_name": tool_name,
            "decision": decision,
            "risk_score": risk_score,
            "details": details or {},
            "prev_hash": last["hash"] if last else "GENESIS",
        }
        entry["hash"] = _hash_entry(entry)
        conn.execute(
            "INSERT INTO audit_log (idx, timestamp, agent_id, tool_name, decision,"
            " risk_score, details, prev_hash, hash) VALUES (?,?,?,?,?,?,?,?,?)",
            (entry["index"], entry["timestamp"], agent_id, tool_name, decision,
             risk_score, json.dumps(entry["details"], sort_keys=True),
             entry["prev_hash"], entry["hash"]),
        )
    return entry

def get_entries():
    with db() as conn:
        rows = conn.execute("SELECT * FROM audit_log ORDER BY idx").fetchall()
    return [_row_to_entry(r) for r in rows]

def verify_log():
    """Returns (True, None) if intact, else (False, index_of_first_bad_entry)."""
    prev_hash = "GENESIS"
    for position, entry in enumerate(get_entries()):
        body = {k: v for k, v in entry.items() if k != "hash"}
        if (entry["index"] != position
                or entry["prev_hash"] != prev_hash
                or _hash_entry(body) != entry["hash"]):
            return False, entry["index"]
        prev_hash = entry["hash"]
    return True, None