"""
Meta WhatsApp Cloud API client.

Unlike Twilio, sending a reply is a separate outbound API call — receiving
a webhook and replying to it are two independent actions, not one round trip.
"""

import httpx

from app.config import META_ACCESS_TOKEN, META_PHONE_NUMBER_ID

GRAPH_API_URL = f"https://graph.facebook.com/v22.0/{META_PHONE_NUMBER_ID}/messages"


def send_text(to: str, body: str) -> dict:
    """
    Sends a plain text WhatsApp message via Meta Cloud API.

    Args:
        to: recipient's phone number, digits only with country code,
            no '+' and no 'whatsapp:' prefix (e.g. "923001234567").
        body: message text.
    """
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }

    response = httpx.post(GRAPH_API_URL, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()
