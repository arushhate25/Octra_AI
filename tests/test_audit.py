from app.gateway import execute
from app.audit import AUDIT_LOG, verify_log

def test_every_decision_is_logged():
    before = len(AUDIT_LOG)
    execute("support_agent", "read_masked_customer", customer_id="C001")
    execute("support_agent", "initiate_transfer",
            from_id="C001", to_id="C002", amount=1)
    assert len(AUDIT_LOG) == before + 2
    assert AUDIT_LOG[-1]["decision"] == "deny"

def test_log_chain_is_valid():
    execute("support_agent", "read_masked_customer", customer_id="C001")
    ok, bad_index = verify_log()
    assert ok

def test_tampering_is_detected():
    execute("support_agent", "initiate_transfer",
            from_id="C001", to_id="C002", amount=1)   # logged as deny
    original = AUDIT_LOG[-1]["decision"]
    try:
        AUDIT_LOG[-1]["decision"] = "allow"   # attacker rewrites history
        ok, bad_index = verify_log()
        assert not ok
    finally:
        AUDIT_LOG[-1]["decision"] = original  # restore so other tests stay valid