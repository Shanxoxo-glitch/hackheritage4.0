import logging
import httpx
from app.config import settings

logger = logging.getLogger("ivrs_gateway")

class IVRSGatewayService:
    @staticmethod
    async def send_sms(to_phone: str, message: str) -> dict:
        """
        Dispatches an SMS notification to the victim.
        Uses Twilio API if credentials are provided; falls back to Mock Mode in dev.
        """
        if settings.TWILIO_MOCK_MODE or not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN):
            logger.info(f"[MOCK TELEPHONY SMS] Sent to '{to_phone}': {message}")
            return {
                "status": "MOCK_SENT",
                "to": to_phone,
                "message": message,
                "provider": "MockTelephonyGateway"
            }

        # Live Twilio REST API dispatch
        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
        auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        payload = {
            "From": settings.TWILIO_PHONE_NUMBER,
            "To": to_phone,
            "Body": message
        }

        async with httpx.AsyncClient() as client:
            res = await client.post(url, data=payload, auth=auth)
            if res.status_code in (200, 201):
                return {"status": "LIVE_SENT", "twilio_sid": res.json().get("sid"), "to": to_phone}
            else:
                logger.error(f"Twilio SMS Error: {res.text}")
                return {"status": "FAILED", "error": res.text}

    @staticmethod
    async def trigger_voice_call(to_phone: str, twiml_url: str | None = None) -> dict:
        """
        Triggers an outbound IVRS voice call to the victim or assigned official.
        """
        if settings.TWILIO_MOCK_MODE or not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN):
            logger.info(f"[MOCK TELEPHONY VOICE CALL] Triggered to '{to_phone}' with TwiML: {twiml_url}")
            return {
                "status": "MOCK_CALL_TRIGGERED",
                "to": to_phone,
                "twiml_url": twiml_url,
                "provider": "MockTelephonyGateway"
            }

        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Calls.json"
        auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        payload = {
            "From": settings.TWILIO_PHONE_NUMBER,
            "To": to_phone,
            "Url": twiml_url or "http://demo.twilio.com/docs/voice.xml"
        }

        async with httpx.AsyncClient() as client:
            res = await client.post(url, data=payload, auth=auth)
            if res.status_code in (200, 201):
                return {"status": "LIVE_CALL_TRIGGERED", "twilio_sid": res.json().get("sid"), "to": to_phone}
            else:
                logger.error(f"Twilio Voice Call Error: {res.text}")
                return {"status": "FAILED", "error": res.text}
