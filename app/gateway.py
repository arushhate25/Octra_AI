from app.tools import TOOLS
from app.risk import risk_score, decide
from app.approvals import request_approval, consume_approval, action_fingerprint
from app.audit import log_event
from app.inventory import allowed_tools, is_revoked


def _execute(agent_id, tool_name, approval_id=None, **kwargs):
    # Kill switch first: a revoked agent can do nothing at all.
    if is_revoked(agent_id):
        return {"decision": "deny",
                "reason": f"{agent_id} is revoked (kill switch active)"}

    # Check 1: is this agent allowed to use this tool?
    allowed = allowed_tools(agent_id)
    if tool_name not in allowed or tool_name not in TOOLS:
        return {"decision": "deny",
                "reason": f"{agent_id} may not use {tool_name}"}

    # Check 2: how risky is the action?
    score = risk_score(tool_name)
    decision = decide(score)

    if decision == "needs_approval":
        if approval_id is None:
            request_id = request_approval(agent_id, tool_name, kwargs, score)
            return {"decision": "needs_approval", "risk_score": score,
                    "request_id": request_id}
        ok, reason = consume_approval(approval_id, agent_id, tool_name, kwargs)
        if not ok:
            return {"decision": "deny", "risk_score": score, "reason": reason}
        result = TOOLS[tool_name](**kwargs)
        return {"decision": "allow", "risk_score": score,
                "result": result, "approved": True}

    if decision != "allow":
        return {"decision": decision, "risk_score": score,
                "reason": "action not auto-approved"}

    result = TOOLS[tool_name](**kwargs)
    return {"decision": "allow", "risk_score": score, "result": result}


def execute(agent_id, tool_name, approval_id=None, **kwargs):
    result = _execute(agent_id, tool_name, approval_id, **kwargs)
    log_event(
        agent_id, tool_name, result["decision"], result.get("risk_score"),
        {
            "reason": result.get("reason"),
            "approved": result.get("approved", False),
            "request_id": result.get("request_id") or approval_id,
            "args_fingerprint": action_fingerprint(agent_id, tool_name, kwargs),
        },
    )
    return result