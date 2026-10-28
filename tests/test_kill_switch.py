from fastapi.testclient import TestClient

from app.main import app
from app.audit import get_entries

client = TestClient(app)

SUPPORT = {"X-API-Key": "test-support-key"}
PAYMENTS = {"X-API-Key": "test-payments-key"}
REVIEWER = {"X-API-Key": "test-reviewer-key"}

READ = {"tool_name": "read_masked_customer",
        "arguments": {"customer_id": "C001"}}
TRANSFER = {"tool_name": "initiate_transfer",
            "arguments": {"from_id": "C001", "to_id": "C002", "amount": 100}}


def test_inventory_lists_agents_with_owner_and_tools():
    agents = client.get("/agents", headers=REVIEWER).json()
    ids = {a["agent_id"] for a in agents}
    assert {"support_agent", "payments_agent"} <= ids
    payments = [a for a in agents if a["agent_id"] == "payments_agent"][0]
    assert "initiate_transfer" in payments["tools"]
    assert payments["status"] == "active"


def test_agents_endpoint_is_reviewer_only():
    assert client.get("/agents", headers=SUPPORT).status_code == 403


def test_revoked_agent_is_blocked_immediately():
    r = client.post("/agents/support_agent/revoke", headers=REVIEWER,
                    json={"reason": "suspicious behaviour"})
    assert r.status_code == 200
    r2 = client.post("/execute", headers=SUPPORT, json=READ)
    assert r2.json()["decision"] == "deny"
    assert "revoked" in r2.json()["reason"]


def test_restore_brings_agent_back():
    client.post("/agents/support_agent/revoke", headers=REVIEWER, json={})
    client.post("/agents/support_agent/restore", headers=REVIEWER)
    r = client.post("/execute", headers=SUPPORT, json=READ)
    assert r.json()["decision"] == "allow"


def test_revoking_invalidates_an_existing_approval():
    rid = client.post("/execute", headers=PAYMENTS, json=TRANSFER).json()["request_id"]
    client.post(f"/approve/{rid}", headers=REVIEWER)
    client.post("/agents/payments_agent/revoke", headers=REVIEWER,
                json={"reason": "compromised"})
    r = client.post("/execute", headers=PAYMENTS,
                    json={**TRANSFER, "approval_id": rid})
    assert r.json()["decision"] == "deny"


def test_kill_switch_actions_are_audited():
    client.post("/agents/support_agent/revoke", headers=REVIEWER,
                json={"reason": "test"})
    last = get_entries()[-1]
    assert last["tool_name"] == "agent_status_change"
    assert last["agent_id"] == "human_reviewer"
    assert last["details"]["target_agent"] == "support_agent"


def test_unknown_agent_cannot_be_revoked():
    r = client.post("/agents/ghost_agent/revoke", headers=REVIEWER, json={})
    assert r.status_code == 404


def test_agent_cannot_revoke_agents():
    r = client.post("/agents/payments_agent/revoke", headers=SUPPORT, json={})
    assert r.status_code == 403