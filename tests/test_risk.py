from app.risk import risk_score, decide

def test_read_is_low_risk():
    assert decide(risk_score("read_masked_customer")) == "allow"

def test_transfer_is_high_risk():
    assert decide(risk_score("initiate_transfer")) in ("needs_approval", "deny")