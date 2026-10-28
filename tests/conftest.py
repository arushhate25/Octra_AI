import pytest

@pytest.fixture(autouse=True)
def api_keys(monkeypatch):
    monkeypatch.setenv("SUPPORT_AGENT_KEY", "test-support-key")
    monkeypatch.setenv("PAYMENTS_AGENT_KEY", "test-payments-key")
    monkeypatch.setenv("REVIEWER_KEY", "test-reviewer-key")