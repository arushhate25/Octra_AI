from app.tools import TOOLS

PERMISSIONS = {
    "support_agent": {"read_masked_customer"},
}

def execute(agent_id, tool_name, **kwargs):
    allowed = PERMISSIONS.get(agent_id, set())
    if tool_name not in allowed or tool_name not in TOOLS:
        return {"decision": "deny",
                "reason": f"{agent_id} may not use {tool_name}"}
    result = TOOLS[tool_name](**kwargs)
    return {"decision": "allow", "result": result}