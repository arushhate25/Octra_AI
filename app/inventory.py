import time

from app.audit import log_event
from app.db import db

# The agent registry: who exists, who owns it, what it is for, what it may use.
INVENTORY = {
    "support_agent": {
        "owner": "Customer Support Team",
        "purpose": "Answers customer questions using masked customer records",
        "tools": {"read_masked_customer"},
    },
    "payments_agent": {
        "owner": "Payments Operations",
        "purpose": "Prepares customer transfers (human approval required)",
        "tools": {"read_masked_customer", "initiate_transfer"},
    },
}


def allowed_tools(agent_id):
    return INVENTORY.get(agent_id, {}).get("tools", set())


def is_revoked(agent_id):
    with db() as conn:
        row = conn.execute(
            "SELECT status FROM agent_status WHERE agent_id = ?", (agent_id,)
        ).fetchone()
    return row is not None and row["status"] == "revoked"


def set_agent_status(agent_id, status, changed_by, reason=""):
    """status is 'revoked' or 'active'. Every change is written to the audit log."""
    if agent_id not in INVENTORY:
        return False, "unknown agent"
    with db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO agent_status"
            " (agent_id, status, reason, changed_by, changed_at)"
            " VALUES (?,?,?,?,?)",
            (agent_id, status, reason, changed_by, time.time()),
        )
    log_event(changed_by, "agent_status_change", status, None,
              {"target_agent": agent_id, "reason": reason})
    return True, status


def list_agents():
    with db() as conn:
        rows = {r["agent_id"]: r for r in
                conn.execute("SELECT * FROM agent_status").fetchall()}
    result = []
    for agent_id, info in INVENTORY.items():
        row = rows.get(agent_id)
        result.append({
            "agent_id": agent_id,
            "owner": info["owner"],
            "purpose": info["purpose"],
            "tools": sorted(info["tools"]),
            "status": row["status"] if row else "active",
            "reason": row["reason"] if row else None,
            "changed_by": row["changed_by"] if row else None,
        })
    return result