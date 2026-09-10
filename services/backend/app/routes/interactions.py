"""
PWA Interactivity Stream Proxy to VM Orchestrator (port 8500).
Receives chat/interaction query from PWA, forwards to VM Orchestrator on port 8500,
and streams/returns the AI response generated from the VM back to the PWA frontend.

VM API (PS-26094 Orchestrator v2.0.0):
  POST /v1/interactions         — sync response
  POST /v1/interactions/stream  — streaming SSE response
  Auth: X-API-Key header
  Channel must be one of: pwa | sms | ivr | email
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
    channel: str = "pwa"   # must be lowercase: pwa | sms | ivr | email
    message: str
    language: str | None = "en"

ORCHESTRATOR_VM_URL = getattr(settings, "ORCHESTRATOR_URL", "http://localhost:8500")
# API key for VM Orchestrator — can be overridden via ORCHESTRATOR_API_KEY env var
ORCHESTRATOR_API_KEY = getattr(settings, "ORCHESTRATOR_API_KEY", "")

def generate_intelligent_response(message: str) -> str:
    msg_lower = message.lower().strip()
    
    if any(kw in msg_lower for kw in ["hello", "hi", "hey", "greetings", "good morning", "good evening"]):
        return (
            "Hello! I am Sahayak, your AI Legal & Distress Support Assistant. "
            "How can I support you today? You can ask me about legal procedures, "
            "filing complaints, victim rights, or emergency protection resources."
        )
    elif any(kw in msg_lower for kw in ["sue", "lawsuit", "court", "lawyer", "advocate", "legal notice", "plaint"]):
        return (
            "To initiate a legal action or civil lawsuit, here are the essential steps and requirements:\n\n"
            "1. **Identify Ground of Action**: Determine if this is a civil dispute (breach of contract, property, defamation) or criminal offense.\n"
            "2. **Gather Documentary Evidence**: Collect all contracts, receipts, written communications, and identity proof.\n"
            "3. **Draft & Send Legal Notice**: Standard procedure requires sending a formal Legal Notice giving 15–30 days for resolution.\n"
            "4. **File Plaint in Court**: If unresolved, an advocate files a formal Plaint in the court with appropriate jurisdiction.\n\n"
            "💡 *Tip: If you need free legal aid, you can connect with NALSA (National Legal Services Authority) or request an advocate through our portal.*"
        )
    elif any(kw in msg_lower for kw in ["help", "emergency", "danger", "police", "abuse", "violence", "threat"]):
        return (
            "⚠️ **Emergency Assistance Resources**:\n\n"
            "- **National Emergency Number**: Dial **112**\n"
            "- **Women Helpline**: Dial **181**\n"
            "- **National Commission for Women**: Dial **1091**\n\n"
            "Your safety is top priority. If you are in immediate danger, please reach a safe location or contact local emergency services immediately."
        )
    else:
        return (
            f"Thank you for sharing your query. Regarding '{message}', Sahayak provides confidential legal guidance, "
            "case tracking, and distress monitoring. Please let me know if you would like to connect with a legal advocate or review active resources."
        )

@router.options("/stream")
async def stream_options():
    return {}

@router.post("/stream")
async def stream_interaction_to_vm(payload: InteractionStreamPayload):
    """
    Proxies user chat query from PWA -> Backend -> Azure VM Orchestrator (:8500),
    and streams the generated AI response back into the PWA UI.
    Falls back gracefully to intelligent local AI assistant when VM tunnel is offline.
    """
    orch_url = getattr(settings, "ORCHESTRATOR_URL", "http://localhost:8500")
    orch_key = getattr(settings, "ORCHESTRATOR_API_KEY", "vk_dev")
    vm_endpoint = f"{orch_url}/v1/interactions"
    channel = payload.channel.lower() if payload.channel else "pwa"

    async def event_generator():
        vm_success = False
        try:
            headers = {"Content-Type": "application/json"}
            if orch_key:
                headers["X-API-Key"] = orch_key

            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    vm_endpoint,
                    json={
                        "case_id": payload.case_id or "demo-case-01",
                        "channel": channel,
                        "message": payload.message,
                        "language": payload.language
                    },
                    headers=headers
                )
                if res.status_code == 200:
                    vm_success = True
                    data = res.json()
                    reply = data.get("reply", data.get("response", data.get("message", "Thank you for sharing. I am here to support you.")))
                    words = reply.split(" ")
                    for word in words:
                        chunk = (word + " ")
                        yield f"data: {json.dumps({'delta': chunk})}\n\n"

                    final_payload = {
                        "thread_id": data.get("thread_id", "thread-vm-8500"),
                        "status": "completed",
                        "audit_ref": data.get("audit_ref", "audit-vm-8500"),
                        "reply": reply,
                        "source": "vm_orchestrator"   # ← tells you this came from VM
                    }
                    yield f"data: {json.dumps({'final': final_payload})}\n\n"
                else:
                    print(f"[Interactions Stream] VM returned status {res.status_code}: {res.text}")
        except Exception as e:
            print(f"[Interactions Stream] VM request error: {e}")
            vm_success = False

        if not vm_success:
            reply = generate_intelligent_response(payload.message)
            words = reply.split(" ")
            for word in words:
                chunk = (word + " ")
                yield f"data: {json.dumps({'delta': chunk})}\n\n"
            yield f"data: {json.dumps({'final': {'thread_id': 'thread-local-fallback', 'status': 'completed', 'audit_ref': 'audit-local', 'reply': reply, 'source': 'local_fallback'}})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
