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