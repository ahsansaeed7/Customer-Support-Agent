"""
Tool registry.
"""

from app.agent.tools.search_tours import search_tours, SEARCH_TOURS_SCHEMA
from app.agent.tools.booking import create_booking_draft, CREATE_BOOKING_DRAFT_SCHEMA
from app.agent.tools.booking_status import (
    confirm_booking_intent, CONFIRM_BOOKING_INTENT_SCHEMA,
    cancel_booking, CANCEL_BOOKING_SCHEMA,
)
from app.agent.tools.payment_info import get_payment_details, GET_PAYMENT_DETAILS_SCHEMA
from app.agent.tools.escalate import escalate_to_human, ESCALATE_TO_HUMAN_SCHEMA

TOOL_SCHEMAS = [
    {"type": "function", "function": SEARCH_TOURS_SCHEMA},
    {"type": "function", "function": CREATE_BOOKING_DRAFT_SCHEMA},
    {"type": "function", "function": CONFIRM_BOOKING_INTENT_SCHEMA},
    {"type": "function", "function": CANCEL_BOOKING_SCHEMA},
    {"type": "function", "function": GET_PAYMENT_DETAILS_SCHEMA},
    {"type": "function", "function": ESCALATE_TO_HUMAN_SCHEMA},
]

TOOL_FUNCTIONS = {
    "search_tours": search_tours,
    "create_booking_draft": create_booking_draft,
    "confirm_booking_intent": confirm_booking_intent,
    "cancel_booking": cancel_booking,
    "get_payment_details": get_payment_details,
    "escalate_to_human": escalate_to_human,
}
