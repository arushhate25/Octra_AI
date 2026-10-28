from app.tools import TOOLS
from app.risk import risk_score, decide
from app.approvals import request_approval, consume_approval

PERMISSIONS = {
    "support_agent": {"read_masked_customer"},
    "payments_agent": {"read_masked_customer", "initiate_transfer"},
}

def execute(agent_id, tool_name, approval_id=None, **kwargs):
    allowed = PERMISSIONS.get(agent_id, set())
    if tool_name not in allowed or tool_name not in TOOLS:
        return {"decision": "deny",
                "reason": f"{agent_id} may not use {tool_name}"}

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