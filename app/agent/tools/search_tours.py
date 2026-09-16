"""
search_tours tool.

Right now this is a plain Python function you can call directly to test —
no LLM involved. Later, `SEARCH_TOURS_SCHEMA` gets passed to the LLM as a
tool definition, and `search_tours(**args)` gets called with whatever
arguments the LLM decides on.
"""

from app.db.session import SessionLocal
from app.db.crud import query_tours


def search_tours(destination: str = None, max_budget: float = None, duration_days: int = None) -> list[dict]:
    """
    Search available tours by destination, budget, and/or duration.
    Returns a list of plain dicts (JSON-serializable) — never raw ORM objects,
    since this will eventually be serialized back to the LLM as a tool result.
    """
    db = SessionLocal()
    try:
        tours = query_tours(
            db,
            destination=destination,
            max_budget=max_budget,
            duration=duration_days,
        )
        return [
            {
                "id": str(t.id),
                "title": t.title,
                "destination": t.destination,
                "duration_days": t.duration_days,
                "base_price": float(t.base_price),
                "currency": t.currency,
                "available_seats": t.available_seats,
                "tags": t.tags,
            }
            for t in tours
        ]
    finally:
        db.close()


# Tool schema — this is what gets handed to the LLM later so it knows
# this tool exists, what it does, and what arguments to pass.
# additionalProperties: false + every key listed in "required" is Groq's/
# OpenAI's strict function-calling requirement — optional-ness is expressed
# via nullable types (["string", "null"]), not by omitting from "required".
SEARCH_TOURS_SCHEMA = {
    "name": "search_tours",
    "description": (
        "Search available travel tour packages by destination, maximum budget, "
        "and/or trip duration. Use this whenever a customer describes what kind "
        "of trip they're looking for. Pass null for any filter the customer "
        "hasn't specified."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "destination": {
                "type": ["string", "null"],
                "description": "Destination name or partial match, e.g. 'Bali' or 'Switzerland'.",
            },
            "max_budget": {
                "type": ["number", "null"],
                "description": "Maximum price in USD the customer wants to spend per person.",
            },
            "duration_days": {
                "type": ["integer", "null"],
                "description": "Desired trip length in days.",
            },
        },
        "required": ["destination", "max_budget", "duration_days"],
        "additionalProperties": False,
    },
}


if __name__ == "__main__":
    # Quick manual test — run with: python -m app.agent.tools.search_tours
    import json

    print("All tours under $1000:")
    print(json.dumps(search_tours(max_budget=1000), indent=2))

    print("\nTours in Bali:")
    print(json.dumps(search_tours(destination="Bali"), indent=2))

    print("\n7-day tours:")
    print(json.dumps(search_tours(duration_days=7), indent=2))
