"""
get_payment_details tool.

Returns your agency's REAL payment instructions from config/env — never
from the LLM's imagination. Add stripe/PayPal links here too once you have
real ones. This exists specifically so the agent never has to invent bank
details, which it will otherwise do if asked and given no real tool for it.
"""

import os

BANK_TRANSFER_DETAILS = {
    "method": "bank_transfer",
    "account_name": os.environ.get("BANK_ACCOUNT_NAME", "SET_ME_IN_ENV"),
    "account_number": os.environ.get("BANK_ACCOUNT_NUMBER", "SET_ME_IN_ENV"),
    "swift_bic": os.environ.get("BANK_SWIFT_BIC", "SET_ME_IN_ENV"),
    "bank_name": os.environ.get("BANK_NAME", "SET_ME_IN_ENV"),
}


def get_payment_details(booking_reference: str, amount: float, currency: str) -> dict:
    """
    Returns real payment instructions to relay to the customer for a
    specific booking. Currently bank transfer only — add Stripe/PayPal
    branches here once those are wired up, still from real config, never
    invented.
    """
    return {
        "booking_reference": booking_reference,
        "amount": amount,
        "currency": currency,
        **BANK_TRANSFER_DETAILS,
    }


GET_PAYMENT_DETAILS_SCHEMA = {
    "name": "get_payment_details",
    "description": (
        "Get the REAL payment instructions (bank account details) for a "
        "specific booking. You must call this tool to get payment details — "
        "never state an account number, SWIFT code, or bank name unless it "
        "came from this tool's result. If this tool is unavailable or "
        "returns an error, tell the customer you'll have a team member send "
        "payment details, and call escalate_to_human — do not invent details."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "booking_reference": {"type": "string", "description": "The booking's reference code, e.g. TRV-1234-A."},
            "amount": {"type": "number", "description": "Total amount due."},
            "currency": {"type": "string", "description": "Currency code, e.g. USD."},
        },
        "required": ["booking_reference", "amount", "currency"],
        "additionalProperties": False,
    },
}
