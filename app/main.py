from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from app.gateway import execute
from app.approvals import approve
from app.audit import get_entries, verify_log
from app.auth import authenticate

app = FastAPI(title="BankGuard AI")

RESERVED_KEYS = {"agent_id", "tool_name", "approval_id"}

def require_role(role):
    def checker(x_api_key: Optional[str] = Header(default=None)):
        identity = authenticate(x_api_key)
        if identity is None:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")
        if identity[0] != role:
            raise HTTPException(status_code=403, detail="Not allowed for this role")
        return identity[1]
    return checker

class ExecuteRequest(BaseModel):
    tool_name: str
    arguments: dict = {}
    approval_id: Optional[str] = None

@app.post("/execute")
def execute_action(req: ExecuteRequest,
                   agent_id: str = Depends(require_role("agent"))):
    if RESERVED_KEYS & req.arguments.keys():
        raise HTTPException(status_code=400, detail="Reserved argument name")
    try:
        return execute(agent_id, req.tool_name,
                       approval_id=req.approval_id, **req.arguments)
    except (TypeError, KeyError):
        raise HTTPException(status_code=400, detail="Invalid tool arguments")

@app.post("/approve/{request_id}")
def approve_request(request_id: str,
                    approver_id: str = Depends(require_role("approver"))):
    ok, reason = approve(request_id, approver_id)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)
    return {"status": "approved", "request_id": request_id}

@app.get("/audit")
def get_audit(_: str = Depends(require_role("approver"))):
    return get_entries

@app.get("/audit/verify")
def verify_audit(_: str = Depends(require_role("approver"))):
    ok, bad_index = verify_log()
    return {"valid": ok, "first_bad_index": bad_index}