import os

import httpx
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv(override=True)


st.set_page_config(page_title="BankGuard AI", layout="wide")

API_URL = st.sidebar.text_input("API URL", "http://127.0.0.1:8000")
API_KEY = os.environ.get("REVIEWER_KEY", "")   # never typed or committed
if st.sidebar.button("Refresh"):
    st.rerun()


def call(method, path, json_body=None):
    r = httpx.request(method, API_URL + path, json=json_body,
                      headers={"X-API-Key": API_KEY}, timeout=5)
    r.raise_for_status()
    return r.json()


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

df = pd.DataFrame(entries)
decisions = df["decision"].value_counts() if not df.empty else {}

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total events", len(df))
c2.metric("Allowed", int(decisions.get("allow", 0)))
c3.metric("Held for approval", int(decisions.get("needs_approval", 0)))
c4.metric("Denied", int(decisions.get("deny", 0)))

if integrity["valid"]:
    st.success("Audit chain intact")
else:
    st.error(f"Audit chain BROKEN at entry {integrity['first_bad_index']}")

# ---- Agent inventory and kill switch ----
st.subheader("Agents")
for ag in agents:
    left, right = st.columns([4, 1])
    state = ":green[ACTIVE]" if ag["status"] == "active" else ":red[REVOKED]"
    left.markdown(f"**{ag['agent_id']}**: {state}")
    left.caption(f"Owner: {ag['owner']} | Purpose: {ag['purpose']} | "
                 f"Tools: {', '.join(ag['tools'])}")
    if ag["status"] == "active":
        if right.button("Revoke", key="revoke-" + ag["agent_id"]):
            call("POST", f"/agents/{ag['agent_id']}/revoke",
                 {"reason": "Revoked from dashboard"})
            st.rerun()
    else:
        if right.button("Restore", key="restore-" + ag["agent_id"]):
            call("POST", f"/agents/{ag['agent_id']}/restore")
            st.rerun()
    st.divider()

# ---- Pending approvals ----
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
    left.caption(f"Request id: {a['request_id']} | expires in {a['seconds_left']}s")
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
        st.dataframe(
            pd.DataFrame(history)[["agent_id", "tool_name", "status",
                                   "approver", "risk_score"]],
            hide_index=True,
        )

# ---- Decisions chart and audit trail ----
if not df.empty:
    st.subheader("Decisions by agent")
    st.bar_chart(df.groupby(["agent_id", "decision"]).size().unstack(fill_value=0))

    st.subheader("Audit trail (newest first)")
    view = df.copy()
    view["time"] = pd.to_datetime(view["timestamp"], unit="s")
    view = view.sort_values("index", ascending=False)
    st.dataframe(
        view[["time", "agent_id", "tool_name", "decision", "risk_score"]],
        hide_index=True,
    )
    with st.expander("Raw log entries (with hashes)"):
        st.json(entries[-20:])