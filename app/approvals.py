import hashlib
import json
import time
import uuid

from app.db import db

APPROVAL_TTL_SECONDS = 300  # 5 minutes

def action_fingerprint(agent_id, tool_name, kwargs):
    payload = json.dumps(
        {"agent": agent_id, "tool": tool_name, "args": kwargs}, sort_keys=True
    )
    return hashlib.sha256(payload.encode()).hexdigest()

def request_approval(agent_id, tool_name, kwargs, risk_score):
    request_id = str(uuid.uuid4())
    with db() as conn:
        conn.execute(
            "INSERT INTO approvals (request_id, fingerprint, agent_id, tool_name,"
            " risk_score, created_at, status, approver)"
            " VALUES (?,?,?,?,?,?, 'pending', NULL)",
            (request_id, action_fingerprint(agent_id, tool_name, kwargs),
             agent_id, tool_name, risk_score, time.time()),
        )
    return request_id

def approve(request_id, approver_id):
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        req = conn.execute(
            "SELECT * FROM approvals WHERE request_id = ?", (request_id,)
        ).fetchone()
        if req is None:
            return False, "unknown request"
        if req["status"] != "pending":
            return False, "request already handled"
        if time.time() - req["created_at"] > APPROVAL_TTL_SECONDS:
            conn.execute("UPDATE approvals SET status='expired' WHERE request_id=?",
                         (request_id,))
            return False, "request expired"
        if approver_id == req["agent_id"]:
            return False, "agent cannot approve its own request"
        conn.execute(
            "UPDATE approvals SET status='approved', approver=? WHERE request_id=?",
            (approver_id, request_id),
        )
        return True, "approved"

def consume_approval(request_id, agent_id, tool_name, kwargs):
    """Called by the gateway just before running. One-time use, atomic."""
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        req = conn.execute(
            "SELECT * FROM approvals WHERE request_id = ?", (request_id,)
        ).fetchone()
        if req is None or req["status"] != "approved":
            return False, "no valid approval"
        if time.time() - req["created_at"] > APPROVAL_TTL_SECONDS:
            conn.execute("UPDATE approvals SET status='expired' WHERE request_id=?",
                         (request_id,))
            return False, "approval expired"
        if req["fingerprint"] != action_fingerprint(agent_id, tool_name, kwargs):
            return False, "action differs from what was approved"
        conn.execute("UPDATE approvals SET status='used' WHERE request_id=?",
                     (request_id,))
        return True, "ok"