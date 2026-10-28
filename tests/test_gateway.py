from app.gateway import execute

def test_allowed_tool_works():
    r = execute("support_agent", "read_masked_customer", customer_id="C001")
    assert r["decision"] == "allow"
    assert r["result"]["account_no"] == "******7890"

def test_transfer_is_denied():
    r = execute("support_agent", "initiate_transfer",
                from_id="C001", to_id="C002", amount=100)
    assert r["decision"] == "deny"

def test_unknown_agent_is_denied():
    r = execute("ghost_agent", "read_masked_customer", customer_id="C001")
    assert r["decision"] == "deny"