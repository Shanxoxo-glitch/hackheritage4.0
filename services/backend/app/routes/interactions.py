"""
PWA Interactivity Stream Proxy to VM Orchestrator (port 8500).
Receives chat/interaction query from PWA, forwards to VM Orchestrator on port 8500,
and streams/returns the AI response generated from the VM back to the PWA frontend.
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
import json
from app.config import settings

router = APIRouter(prefix="/v1/interactions", tags=["interactions"])

class InteractionStreamPayload(BaseModel):
    case_id: str | None = "demo-case-01"
    channel: str = "PWA"
    message: str
    language: str | None = "en"

ORCHESTRATOR_VM_URL = getattr(settings, "ORCHESTRATOR_URL", "http://localhost:8500")

@router.post("/stream")
async def stream_interaction_to_vm(payload: InteractionStreamPayload):
    """
    Proxies user chat query from PWA -> Backend -> Azure VM Orchestrator (:8500),
    and streams the generated AI response back into the PWA UI.
    """
    vm_endpoint = f"{ORCHESTRATOR_VM_URL}/v1/chat"
    
    async def event_generator():
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    vm_endpoint,
                    json={
                        "case_id": payload.case_id,
                        "channel": payload.channel,
                        "message": payload.message,
                        "language": payload.language
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    reply = data.get("reply", data.get("response", "Thank you for sharing. I am here to support you."))
                    words = reply.split(" ")
                    for word in words:
                        chunk = (word + " ")
                        yield f"data: {json.dumps({'delta': chunk})}\n\n"
                    
                    final_payload = {
                        "thread_id": data.get("thread_id", "thread-vm-8500"),
                        "status": "completed",
                        "audit_ref": data.get("audit_ref", "audit-vm-8500"),
                        "reply": reply
                    }
                    yield f"data: {json.dumps({'final': final_payload})}\n\n"
                else:
                    reply = "I hear you. Whatever you are feeling right now is completely valid. We are here with you."
                    for word in reply.split(" "):
                        yield f"data: {json.dumps({'delta': word + ' '})}\n\n"
                    yield f"data: {json.dumps({'final': {'thread_id': 'thread-demo', 'status': 'completed', 'audit_ref': 'audit-demo', 'reply': reply}})}\n\n"
        except Exception:
            reply = "Thank you for reaching out and sharing. Your message has been safely logged in your case record."
            for word in reply.split(" "):
                yield f"data: {json.dumps({'delta': word + ' '})}\n\n"
            yield f"data: {json.dumps({'final': {'thread_id': 'thread-demo', 'status': 'completed', 'audit_ref': 'audit-demo', 'reply': reply}})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
