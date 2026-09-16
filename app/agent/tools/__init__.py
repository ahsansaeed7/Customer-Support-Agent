"""
Tool registry.

Every tool module defines:
  - a plain function (the actual logic)
  - a *_SCHEMA dict (tells the LLM the tool exists, what it does, its args)

This file collects all of them into two things the agent loop needs:
  - TOOL_SCHEMAS: list passed to the Groq API's `tools` parameter
  - TOOL_FUNCTIONS: dict mapping tool name -> the actual callable
"""

from app.agent.tools.search_tours import search_tours, SEARCH_TOURS_SCHEMA
from app.agent.tools.booking import create_booking_draft, CREATE_BOOKING_DRAFT_SCHEMA
from app.agent.tools.booking_status import confirm_booking_intent, CONFIRM_BOOKING_INTENT_SCHEMA
from app.agent.tools.payment_info import get_payment_details, GET_PAYMENT_DETAILS_SCHEMA
from app.agent.tools.escalate import escalate_to_human, ESCALATE_TO_HUMAN_SCHEMA

TOOL_SCHEMAS = [
    {"type": "function", "function": SEARCH_TOURS_SCHEMA},
    {"type": "function", "function": CREATE_BOOKING_DRAFT_SCHEMA},
    {"type": "function", "function": CONFIRM_BOOKING_INTENT_SCHEMA},
    {"type": "function", "function": GET_PAYMENT_DETAILS_SCHEMA},
    {"type": "function", "function": ESCALATE_TO_HUMAN_SCHEMA},
]

TOOL_FUNCTIONS = {
    "search_tours": search_tours,
    "create_booking_draft": create_booking_draft,
    "confirm_booking_intent": confirm_booking_intent,
    "get_payment_details": get_payment_details,
    "escalate_to_human": escalate_to_human,
}
