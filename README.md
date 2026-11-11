# BankGuard AI: Agent Governance Prototype

A reference prototype showing how a bank could let AI agents call tools safely: permissions, risk-based human approval, and a tamper-evident audit trail.

> Simulated project on synthetic data. Results below are from a small simulated test set, not real bank performance. It is not certified or compliant with any regulation.

## Core idea
The agent is never trusted to enforce its own permissions. Every tool call goes through a separate execution gateway.

```mermaid
flowchart LR
    A[AI agent] -->|tool call + API key| G[Execution gateway]
    G --> P{Permitted?}
    P -->|no| D[Deny]
    P -->|yes| R[Risk score]
    R -->|low| T[Run tool]
    R -->|high| H[Hold for human approval]
    R -->|very high| D
    H --> U[Reviewer dashboard]
    U -->|approve| G
    G --> L[(Hash-chained audit log)]
```

## What it does
- **Identity:** API keys map to agent or approver roles (identity comes from the key, never from the request body).
- **Permissions:** each agent can use only its allowed tools.
- **Risk scoring:** weighted 0-100 score decides allow / needs approval / deny.
- **Human approval:** bound to the exact action, expires, single use, and an agent cannot approve itself.
- **Audit log:** hash-chained, stored in SQLite, verifiable through an endpoint.
- **Dashboard:** pending approvals with full details, decision counts, chain integrity.

## Results (simulated)
- Unauthorised-action block rate: 100% (6/6 attack scenarios, simulated)
- False-denial rate on legitimate calls: 0% (simulated)
- Automated tests: 42 passing

## Run it (PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# once: creates a git-ignored .env file with three random keys
python make_env.py

# terminal 1: the API
uvicorn app.main:app --reload

# terminal 2: the dashboard
python -m streamlit run dashboard/dashboard.py

# run the tests
python -m pytest
```
The API runs on http://127.0.0.1:8000 (test page at /docs). The dashboard runs on http://localhost:8501.

## Documentation
- [Threat model](docs/threat_model.md)
- [Control matrix](docs/control_matrix.md)

## Known limitations
- API keys instead of OAuth 2.0 / OpenID Connect; no key rotation; no login on the dashboard.
- Hash chaining is tamper-evident, not tamper-proof. Removing the newest entries is not detected without an external anchor.
- Static role-based permissions only; no attribute-based rules.
- SQLite for the prototype; a real system would use a hardened database.
- Small attack set, synthetic data only.

## Roadmap
Kill switch, agent inventory, OAuth/OIDC, external hash anchoring, more attack scenarios.