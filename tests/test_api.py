from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

TRANSFER = {
    "agent_id": "payments_agent",
    "tool_name": "initiate_transfer",
    "arguments": {"from_id": "C001", "to_id": "C002", "amount": 100},
}

def test_execute_allowed():
    r = client.post("/execute", json={
        "agent_id": "support_agent",
        "tool_name": "read_masked_customer",
        "arguments": {"customer_id": "C001"},
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "allow"

def test_transfer_approval_flow_over_api():
    r = client.post("/execute", json=TRANSFER)
    assert r.json()["decision"] == "needs_approval"
    rid = r.json()["request_id"]
    a = client.post(f"/approve/{rid}", json={"approver_id": "human_reviewer"})
    assert a.status_code == 200
    r2 = client.post("/execute", json={**TRANSFER, "approval_id": rid})
    assert r2.json()["decision"] == "allow"

def test_reserved_argument_names_rejected():
    r = client.post("/execute", json={
        "agent_id": "support_agent",
        "tool_name": "read_masked_customer",
        "arguments": {"agent_id": "admin", "customer_id": "C001"},
    })
    assert r.status_code == 400

def test_audit_verify_endpoint():
    r = client.get("/audit/verify")
    assert r.json()["valid"] is True