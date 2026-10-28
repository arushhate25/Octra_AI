# Control-to-requirement matrix

Mapping only. This is not evidence of compliance. Verify framework IDs against the official sources.

| Control | Where | OWASP agentic risk | NIST AI RMF function | EU AI Act | Status |
|---|---|---|---|---|---|
| Agent identity and roles | auth.py, main.py | Identity and privilege abuse | Govern, Manage | Art. 15 (cybersecurity) | Partial: API keys, no OAuth/OIDC, no rotation |
| Permission list | gateway.py | Tool misuse, privilege abuse | Manage | Art. 15 | Covered for prototype (static roles only) |
| Risk scoring | risk.py | Tool misuse | Measure, Manage | Art. 9 (risk management) | Partial: design-choice weights, not validated |
| Human approval | approvals.py, dashboard | Goal hijack containment | Govern, Manage | Art. 14 (human oversight) | Covered for prototype (no SSO/MFA) |
| Audit trail | audit.py | Rogue agents | Measure, Govern | Art. 12 (record-keeping) | Partial: tamper-evident, tail removal undetected |
| Data minimisation | tools.py, audit.py | Sensitive data exposure | Map, Manage | UK GDPR data minimisation | Partial: synthetic data only |
| Adversarial testing | test_adversarial.py | Tested rows in threat model | Measure | Art. 15 | Partial: small scenario set |
| Kill switch | none | Rogue agents | Manage | none | Not implemented |
| Agent inventory | none | none | Govern, Map | none | Not implemented |
| Memory poisoning, inter-agent communication, supply chain, code execution, cascading failures | none | Several | none | none | Not covered |