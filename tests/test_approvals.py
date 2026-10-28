from app.gateway import execute
from app.approvals import approve, PENDING

ARGS = dict(from_id="C001", to_id="C002", amount=100)

def new_request():
    return execute("payments_agent", "initiate_transfer", **ARGS)["request_id"]

def test_full_approval_flow():
    rid = new_request()
    ok, _ = approve(rid, "human_reviewer")
    assert ok
    r = execute("payments_agent", "initiate_transfer", approval_id=rid, **ARGS)
    assert r["decision"] == "allow"

def test_unapproved_request_cannot_run():
    rid = new_request()
    r = execute("payments_agent", "initiate_transfer", approval_id=rid, **ARGS)
    assert r["decision"] == "deny"

def test_modified_action_is_rejected():
    rid = new_request()
    approve(rid, "human_reviewer")
    r = execute("payments_agent", "initiate_transfer", approval_id=rid,
                from_id="C001", to_id="C002", amount=9999)
    assert r["decision"] == "deny"

def test_approval_cannot_be_replayed():
    rid = new_request()
    approve(rid, "human_reviewer")
    execute("payments_agent", "initiate_transfer", approval_id=rid, **ARGS)
    r = execute("payments_agent", "initiate_transfer", approval_id=rid, **ARGS)
    assert r["decision"] == "deny"

def test_agent_cannot_approve_itself():
    rid = new_request()
    ok, _ = approve(rid, "payments_agent")
    assert not ok

def test_expired_approval_is_rejected():
    rid = new_request()
    approve(rid, "human_reviewer")
    PENDING[rid]["created_at"] -= 1000   # pretend 1000 seconds have passed
    r = execute("payments_agent", "initiate_transfer", approval_id=rid, **ARGS)
    assert r["decision"] == "deny"