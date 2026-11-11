
import os
from datetime import datetime

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv(override=True)

st.set_page_config(page_title="BankGuard AI", layout="wide")

API_URL = st.sidebar.text_input("API URL", "http://127.0.0.1:8000")
API_KEY = os.environ.get("REVIEWER_KEY", "")

if st.sidebar.button("Refresh"):
    st.rerun()


def call(method, path, json_body=None):
    response = httpx.request(
        method, API_URL + path, json=json_body,
        headers={"X-API-Key": API_KEY}, timeout=5
    )
    response.raise_for_status()
    return response.json()


st.title("BankGuard AI: Agent Governance Console")
st.caption("Simulated bank. Synthetic data only.")

try:
    entries = call("GET", "/audit")
    integrity = call("GET", "/audit/verify")
    approvals = call("GET", "/approvals")
    agents = call("GET", "/agents")
except Exception as e:
    st.error(f"Cannot reach the API or the reviewer key is wrong: {e}")
    st.stop()

decisions = {}
for entry in entries:
    decision = entry.get("decision")
    decisions[decision] = decisions.get(decision, 0) + 1

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total events", len(entries))
c2.metric("Allowed", decisions.get("allow", 0))
c3.metric("Held for approval", decisions.get("needs_approval", 0))
c4.metric("Denied", decisions.get("deny", 0))

if integrity["valid"]:
    st.success("Audit chain intact")
else:
    st.error(f"Audit chain BROKEN at entry {integrity['first_bad_index']}")

st.subheader("Agents")
for ag in agents:
    left, right = st.columns([4, 1])
    state = ":green[ACTIVE]" if ag["status"] == "active" else ":red[REVOKED]"
    left.markdown(f"**{ag['agent_id']}**: {state}")
    left.caption(
        f"Owner: {ag['owner']} | Purpose: {ag['purpose']} | "
        f"Tools: {', '.join(ag['tools'])}"
    )

    action = "Revoke" if ag["status"] == "active" else "Restore"
    if right.button(action, key=f"{action.lower()}-{ag['agent_id']}"):
        path = f"/agents/{ag['agent_id']}/{action.lower()}"
        body = {"reason": "Revoked from dashboard"} if action == "Revoke" else None
        call("POST", path, body)
        st.rerun()
    st.divider()

pending = [a for a in approvals if a["status"] == "pending"]
st.subheader(f"Pending approvals ({len(pending)})")

if not pending:
    st.write("Nothing waiting for review.")

for a in pending:
    left, right = st.columns([4, 1])
    left.markdown(
        f"**{a['agent_id']}** wants to run **{a['tool_name']}** "
        f"(risk {a['risk_score']:.0f}/100)"
    )
    left.json(a["arguments"])
    left.caption(
        f"Request id: {a['request_id']} | expires in {a['seconds_left']}s"
    )

    if right.button("Approve", key=a["request_id"]):
        try:
            call("POST", f"/approve/{a['request_id']}")
            st.rerun()
        except httpx.HTTPStatusError as e:
            st.error(e.response.json().get("detail", "Approval failed"))
    st.divider()

history = [a for a in approvals if a["status"] != "pending"]
with st.expander(f"Approval history ({len(history)})"):
    if history:
        st.dataframe([
            {key: a.get(key) for key in (
                "agent_id", "tool_name", "status", "approver", "risk_score"
            )}
            for a in history
        ], hide_index=True)

if entries:
    st.subheader("Decisions by agent")
    chart_data = {}
    for entry in entries:
        agent = entry.get("agent_id", "unknown")
        decision = entry.get("decision", "unknown")
        chart_data.setdefault(agent, {})
        chart_data[agent][decision] = chart_data[agent].get(decision, 0) + 1
    st.bar_chart(chart_data)

    st.subheader("Audit trail (newest first)")
    view = sorted(entries, key=lambda e: e.get("index", 0), reverse=True)
    st.dataframe([
        {
            "time": datetime.fromtimestamp(e["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"),
            "agent_id": e.get("agent_id"),
            "tool_name": e.get("tool_name"),
            "decision": e.get("decision"),
            "risk_score": e.get("risk_score"),
        }
        for e in view
    ], hide_index=True)

    with st.expander("Raw log entries (with hashes)"):
        st.json(entries[-20:])
