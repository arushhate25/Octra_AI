import hashlib
import json
import time
import uuid

PENDING = {}
APPROVAL_TTL_SECONDS = 300  # 5 minutes

def action_fingerprint(agent_id, tool_name, kwargs):
    payload = json.dumps(
        {"agent": agent_id, "tool": tool_name, "args": kwargs}, sort_keys=True
    )
    return hashlib.sha256(payload.encode()).hexdigest()

def request_approval(agent_id, tool_name, kwargs, risk_score):
    request_id = str(uuid.uuid4())
    PENDING[request_id] = {
        "fingerprint": action_fingerprint(agent_id, tool_name, kwargs),
        "agent_id": agent_id,
        "tool_name": tool_name,
        "risk_score": risk_score,
        "created_at": time.time(),
        "status": "pending",
        "approver": None,
    }
    return request_id

def approve(request_id, approver_id):
    req = PENDING.get(request_id)
    if req is None:
        return False, "unknown request"
    if req["status"] != "pending":
        return False, "request already handled"
    if time.time() - req["created_at"] > APPROVAL_TTL_SECONDS:
        req["status"] = "expired"
        return False, "request expired"
    if approver_id == req["agent_id"]:
        return False, "agent cannot approve its own request"
    req["status"] = "approved"
    req["approver"] = approver_id
    return True, "approved"

def consume_approval(request_id, agent_id, tool_name, kwargs):
    """Called by the gateway just before running. One-time use."""
    req = PENDING.get(request_id)
    if req is None or req["status"] != "approved":
        return False, "no valid approval"
    if time.time() - req["created_at"] > APPROVAL_TTL_SECONDS:
        req["status"] = "expired"
        return False, "approval expired"
    if req["fingerprint"] != action_fingerprint(agent_id, tool_name, kwargs):
        return False, "action differs from what was approved"
    req["status"] = "used"
    return True, "ok"