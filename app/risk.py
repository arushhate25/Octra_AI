# Each factor is scored 0-100 for the action.
WEIGHTS = {
    "data_sensitivity": 0.25,
    "privilege": 0.25,
    "financial_impact": 0.20,
    "irreversibility": 0.15,
    "external_exposure": 0.15,
}

# Starter scores per tool. These are design choices, so you can adjust them later.
TOOL_RISK = {
    "read_masked_customer": {
        "data_sensitivity": 20, "privilege": 10, "financial_impact": 0,
        "irreversibility": 0, "external_exposure": 0,
    },
    "initiate_transfer": {
        "data_sensitivity": 60, "privilege": 80, "financial_impact": 90,
        "irreversibility": 90, "external_exposure": 70,
    },
}

def risk_score(tool_name):
    factors = TOOL_RISK[tool_name]
    return sum(WEIGHTS[f] * factors[f] for f in WEIGHTS)

def decide(score):
    if score < 30:
        return "allow"
    if score < 60:
        return "restrict"
    if score < 80:
        return "needs_approval"
    return "deny"