from app.tools import TOOLS
from app.risk import risk_score, decide

PERMISSIONS = {
    "support_agent": {"read_masked_customer"},
    "payments_agent": {"read_masked_customer", "initiate_transfer"},
}

def execute(agent_id, tool_name, **kwargs):
    # Check 1: is this agent allowed to use this tool at all?
    allowed = PERMISSIONS.get(agent_id, set())
    if tool_name not in allowed or tool_name not in TOOLS:
        return {"decision": "deny",
                "reason": f"{agent_id} may not use {tool_name}"}

    # Check 2: how risky is the action?
    score = risk_score(tool_name)
    decision = decide(score)

    # Only low-risk actions run automatically. Everything else waits.
    if decision != "allow":
        return {"decision": decision, "risk_score": score,
                "reason": "action not auto-approved"}

    result = TOOLS[tool_name](**kwargs)
    return {"decision": "allow", "risk_score": score, "result": result}