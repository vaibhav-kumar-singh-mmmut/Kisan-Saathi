from fastapi import APIRouter, Request
from typing import Dict, Any

router = APIRouter()

@router.post("/sms/fallback", summary="SMS Fallback Stub")
async def sms_fallback(payload: Dict[str, Any]):
    """
    Stub for sending an SMS via a fallback provider if push notifications fail.
    """
    # Just a stub: log and return success
    return {"status": "success", "message": "SMS fallback triggered (stub)", "payload": payload}

@router.post("/whatsapp/webhook", summary="WhatsApp Webhook Stub")
async def whatsapp_webhook(request: Request):
    """
    Stub webhook to receive and acknowledge WhatsApp Business API messages.
    """
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    return {"status": "received", "message": "WhatsApp webhook triggered (stub)", "payload": payload}
