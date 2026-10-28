from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.gateway import execute
from app.approvals import approve
from app.audit import AUDIT_LOG, verify_log

app = FastAPI(title="OCTRA AI")

RESERVED_KEYS = {"agent_id", "tool_name", "approval_id"}

class ExecuteRequest(BaseModel):
    agent_id: str
    tool_name: str
    arguments: dict = {}
    approval_id: Optional[str] = None

class ApproveRequest(BaseModel):
    approver_id: str

@app.post("/execute")
def execute_action(req: ExecuteRequest):
    # An agent must not smuggle control fields inside the tool arguments.
    if RESERVED_KEYS & req.arguments.keys():
        raise HTTPException(status_code=400, detail="Reserved argument name")
    try:
        return execute(req.agent_id, req.tool_name,
                       approval_id=req.approval_id, **req.arguments)
    except (TypeError, KeyError):
        # Fail closed: bad arguments never run, and never crash the server.
        raise HTTPException(status_code=400, detail="Invalid tool arguments")

@app.post("/approve/{request_id}")
def approve_request(request_id: str, req: ApproveRequest):
    ok, reason = approve(request_id, req.approver_id)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)
    return {"status": "approved", "request_id": request_id}

@app.get("/audit")
def get_audit():
    return AUDIT_LOG

@app.get("/audit/verify")
def verify_audit():
    ok, bad_index = verify_log()
    return {"valid": ok, "first_bad_index": bad_index}