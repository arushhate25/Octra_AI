from app.gateway import execute
from app.audit import get_entries, verify_log
from app.db import db

def test_every_decision_is_logged():
    execute("support_agent", "read_masked_customer", customer_id="C001")
    execute("support_agent", "initiate_transfer",
            from_id="C001", to_id="C002", amount=1)
    entries = get_entries()
    assert len(entries) == 2
    assert entries[-1]["decision"] == "deny"

def test_log_chain_is_valid():
    execute("support_agent", "read_masked_customer", customer_id="C001")
    ok, bad_index = verify_log()
    assert ok

def test_tampering_is_detected():
    execute("support_agent", "initiate_transfer",
            from_id="C001", to_id="C002", amount=1)   # logged as deny
    with db() as conn:   # attacker edits the database file directly
        conn.execute("UPDATE audit_log SET decision = 'allow' WHERE idx = 0")
    ok, bad_index = verify_log()
    assert not ok
    assert bad_index == 0

def test_log_is_stored_in_the_database_file():
    execute("support_agent", "read_masked_customer", customer_id="C001")
    with db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    assert count == 1