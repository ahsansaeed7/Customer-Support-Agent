"""
Meta WhatsApp Cloud API webhook.

Two responsibilities, unlike Twilio's single POST-and-reply flow:

  1. GET /webhook/whatsapp — Meta's one-time verification handshake.
     Meta sends a challenge token; you must echo it back exactly, or Meta
     refuses to register your webhook at all.

  2. POST /webhook/whatsapp — actual inbound messages. Payload is nested
     JSON (not Twilio's flat form fields). We acknowledge receipt with a
     quick 200 OK first (per the 2-second SLA from your original spec),
     then send the reply as a SEPARATE outbound API call via whatsapp/client.py
     — receiving and replying are not the same round trip here.
"""

from fastapi import APIRouter, Request, Query
from fastapi.responses import PlainTextResponse

from app.config import META_VERIFY_TOKEN
from app.agent.loop import run_agent_turn
from app.agent.state import load_history, save_history
from app.whatsapp.client import send_text

router = APIRouter()


@router.get("/webhook/whatsapp")
def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
):
    """One-time handshake Meta performs when you first set the webhook URL."""
    if hub_mode == "subscribe" and hub_verify_token == META_VERIFY_TOKEN:
        return PlainTextResponse(content=hub_challenge)
    return PlainTextResponse(content="Verification failed", status_code=403)


@router.post("/webhook/whatsapp")
async def receive_message(request: Request):
    payload = await request.json()

    try:
        entry = payload["entry"][0]
        change = entry["changes"][0]["value"]
        message = change["messages"][0]
        phone_number = message["from"]
        user_message = message["text"]["body"]
    except (KeyError, IndexError):
        # Not an actual text message (could be a status update, read
        # receipt, etc.) — acknowledge and ignore, nothing to reply to.
        return {"status": "ignored"}

    history = load_history(phone_number)
    reply, updated_history = run_agent_turn(phone_number, user_message, history)
    save_history(phone_number, updated_history)

    send_text(to=phone_number, body=reply)

    return {"status": "ok"}
