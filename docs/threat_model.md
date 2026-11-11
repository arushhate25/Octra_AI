# Threat Model

Scope: a simulated prototype on synthetic data. "Blocked" means the automated test passes, not that the system is proven secure.

## What we protect
- Money movement and customer data reachable through agent tools.
- The audit log (the record of what happened).
- The approval step (the human decision).

## Who we do not trust
- The AI agent. It can be tricked by text it reads, so it never enforces its own rules.
- The request body. Identity comes from the API key only.

## Attacks and controls

| # | Attack simulated | Control | Test | Result |
|---|---|---|---|---|
| 1 | Injected note tells the agent to move money (goal hijack) | Gateway checks permission and risk outside the agent; transfer needs a human | tests/test_adversarial.py::test_prompt_injection_cannot_move_money | Blocked |
| 2 | Agent claims to be another agent in the request body | Identity comes from the API key, not the body | tests/test_api.py::test_agent_identity_comes_from_key_not_body | Blocked |
| 3 | Agent approves its own transfer | Agent role cannot call approve; approver must differ | tests/test_approvals.py::test_agent_cannot_approve_itself | Blocked |
| 4 | Recipient or amount changed after approval | Approval is bound to a SHA-256 fingerprint of agent, tool and arguments | tests/test_approvals.py::test_modified_action_is_rejected | Blocked |
| 5 | Same approval reused (replay) | Single use; consumed on first run | tests/test_approvals.py::test_approval_cannot_be_replayed | Blocked |
| 6 | Old approval used later | 300 second expiry | tests/test_approvals.py::test_expired_approval_is_rejected | Blocked |
| 7 | Agent runs a tool it is not allowed to use | Deny by default; per-agent tool list | tests/test_gateway.py::test_unknown_agent_is_denied | Blocked |
| 8 | Reserved argument names used to bypass checks | Reserved names rejected at the API | tests/test_api.py::test_reserved_argument_names_rejected | Blocked |
| 9 | Rogue agent keeps working | Kill switch checked first on every call; revoking also invalidates its pending approvals | tests/test_kill_switch.py::test_revoked_agent_is_blocked_immediately | Blocked |
| 10 | Audit entry edited | Hash chain breaks; verify endpoint reports it | tests/test_audit.py::test_tampering_is_detected | Detected |
| 11 | Audit entry deleted from the middle | Chain breaks at the gap | tests/test_adversarial.py::test_deleted_audit_entry_is_detected | Detected |
| 12 | Full account number leaks in a response | Output is masked | tests/test_adversarial.py::test_full_account_number_never_exposed | Blocked |
| 13 | Human key used to run tools | Approver role cannot call /execute | tests/test_adversarial.py::test_human_key_cannot_run_tools | Blocked |

## Not covered yet
- Removing the newest audit entries is not detected without an external anchor.
- Approval spam: an agent can create many pending requests.
- Risk score ignores the amount.
- Audit entry is written after the tool runs, so a crash could lose it.
- No login on the dashboard; API keys instead of OAuth; no key rotation.
- Small attack set, no real LLM agent tested.

## Standards (mapped, not certified)
Controls align with OWASP agentic and LLM risks, NIST AI RMF and MITRE ATLAS themes. Check exact IDs against the official sources before quoting them.