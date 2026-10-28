from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SUPPORT = {"X-API-Key": "test-support-key"}
PAYMENTS = {"X-API-Key": "test-payments-key"}
REVIEWER = {"X-API-Key": "test-reviewer-key"}

READ = {"tool_name": "read_masked_customer",
        "arguments": {"customer_id": "C001"}}
TRANSFER = {"tool_name": "initiate_transfer",
            "arguments": {"from_id": "C001", "to_id": "C002", "amount": 100}}

def test_no_key_is_rejected():
    assert client.post("/execute", json=READ).status_code == 401

def test_wrong_key_is_rejected():
    r = client.post("/execute", json=READ, headers={"X-API-Key": "nope"})
    assert r.status_code == 401

def test_execute_allowed():
    r = client.post("/execute", json=READ, headers=SUPPORT)
    assert r.status_code == 200
    assert r.json()["decision"] == "allow"

def test_agent_identity_comes_from_key_not_body():
    # support agent pretends to be the payments agent in the body
    r = client.post("/execute", headers=SUPPORT,
                    json={**TRANSFER, "agent_id": "payments_agent"})
    assert r.json()["decision"] == "deny"

def test_agent_cannot_approve():
    r = client.post("/approve/some-id", headers=PAYMENTS)
    assert r.status_code == 403

def test_transfer_approval_flow_over_api():
    r = client.post("/execute", json=TRANSFER, headers=PAYMENTS)
    assert r.json()["decision"] == "needs_approval"
    rid = r.json()["request_id"]
    a = client.post(f"/approve/{rid}", headers=REVIEWER)
    assert a.status_code == 200
    r2 = client.post("/execute", headers=PAYMENTS,
                     json={**TRANSFER, "approval_id": rid})
    assert r2.json()["decision"] == "allow"

def test_reserved_argument_names_rejected():
    r = client.post("/execute", headers=SUPPORT, json={
        "tool_name": "read_masked_customer",
        "arguments": {"agent_id": "admin", "customer_id": "C001"},
    })
    assert r.status_code == 400

def test_audit_access_is_restricted():
    assert client.get("/audit/verify", headers=SUPPORT).status_code == 403
    r = client.get("/audit/verify", headers=REVIEWER)
    assert r.json()["valid"] is True