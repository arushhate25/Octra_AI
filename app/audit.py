import hashlib
import json
import time

AUDIT_LOG = []

def _hash_entry(entry_body):
    payload = json.dumps(entry_body, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()

def log_event(agent_id, tool_name, decision, risk_score=None, details=None):
    prev_hash = AUDIT_LOG[-1]["hash"] if AUDIT_LOG else "GENESIS"
    entry = {
        "index": len(AUDIT_LOG),
        "timestamp": time.time(),
        "agent_id": agent_id,
        "tool_name": tool_name,
        "decision": decision,
        "risk_score": risk_score,
        "details": details or {},
        "prev_hash": prev_hash,
    }
    entry["hash"] = _hash_entry(entry)
    AUDIT_LOG.append(entry)
    return entry

def verify_log():
    """Returns (True, None) if the chain is intact, else (False, index_of_first_bad_entry)."""
    prev_hash = "GENESIS"
    for entry in AUDIT_LOG:
        body = {k: v for k, v in entry.items() if k != "hash"}
        if entry["prev_hash"] != prev_hash or _hash_entry(body) != entry["hash"]:
            return False, entry["index"]
        prev_hash = entry["hash"]
    return True, None 