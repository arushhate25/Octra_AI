import pytest
from app.db import db

@pytest.fixture(autouse=True)
def api_keys(monkeypatch):
    monkeypatch.setenv("SUPPORT_AGENT_KEY", "test-support-key")
    monkeypatch.setenv("PAYMENTS_AGENT_KEY", "test-payments-key")
    monkeypatch.setenv("REVIEWER_KEY", "test-reviewer-key")

@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setenv("BANKGUARD_DB", str(tmp_path / "test.db"))

@pytest.fixture
def age_approval():
    """Pretends an approval was created `seconds` ago."""
    def _age(request_id, seconds):
        with db() as conn:
            conn.execute(
                "UPDATE approvals SET created_at = created_at - ? WHERE request_id = ?",
                (seconds, request_id),
            )
    return _age


from app.gateway import execute
from app.approvals import approve

ARGS = {"from_id": "C001", "to_id": "C002", "amount": 100}


def new_request():
    result = execute("payments_agent", "initiate_transfer", **ARGS)
    assert "request_id" in result, result
    return result["request_id"]


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
    r = execute(
        "payments_agent", "initiate_transfer",
        approval_id=rid, from_id="C001", to_id="C002", amount=9999
    )
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


def test_expired_approval_is_rejected(age_approval):
    rid = new_request()
    approve(rid, "human_reviewer")
    age_approval(rid, 1000)
    r = execute("payments_agent", "initiate_transfer", approval_id=rid, **ARGS)
    assert r["decision"] == "deny"