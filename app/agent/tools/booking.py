"""
create_booking_draft tool.

Turns a selected tour into a real 'draft' booking row. Finds or creates the
user by phone number (lazily — only at this point, not on every message).
Total price is computed here, server-side — never left for the LLM to invent.
"""

import random
import string

from app.db.session import SessionLocal
from app.db.crud import get_or_create_user, get_tour_by_id
from app.db.models import Booking


def _generate_booking_reference() -> str:
    """e.g. TRV-8921-X — matches the format from the original spec."""
    digits = "".join(random.choices(string.digits, k=4))
    letter = random.choice(string.ascii_uppercase)
    return f"TRV-{digits}-{letter}"


def create_booking_draft(
    phone_number: str,
    tour_id: str,
    travel_date: str,
    pax_count: int | None = 1,
) -> dict:
    """
    Create a draft booking for a given tour.

    Args:
        phone_number: customer's WhatsApp number, used as their identity.
        tour_id: UUID of the tour (from a prior search_tours result).
        travel_date: ISO date string, e.g. "2026-11-20".
        pax_count: number of travelers.

    Returns a dict describing the created booking, or an error dict if the
    tour doesn't exist or doesn't have enough seats.
    """
    if pax_count is None:
        pax_count = 1

    db = SessionLocal()
    try:
        tour = get_tour_by_id(db, tour_id)
        if tour is None:
            return {"error": "Tour not found."}

        if tour.available_seats < pax_count:
            return {"error": f"Only {tour.available_seats} seats left for this tour."}

        user = get_or_create_user(db, phone_number)

        total_amount = float(tour.base_price) * pax_count

        # Keep generating a reference until we get one that isn't already taken —
        # collisions are extremely unlikely but cheap to guard against.
        for _ in range(5):
            reference = _generate_booking_reference()
            if not db.query(Booking).filter_by(booking_reference=reference).first():
                break
        else:
            return {"error": "Could not generate a unique booking reference, try again."}

        booking = Booking(
            booking_reference=reference,
            user_id=user.id,
            tour_id=tour.id,
            travel_date=travel_date,
            pax_count=pax_count,
            total_amount=total_amount,
            currency=tour.currency,
            status="draft",
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)

        return {
            "booking_id": str(booking.id),
            "booking_reference": booking.booking_reference,
            "tour_title": tour.title,
            "travel_date": travel_date,
            "pax_count": pax_count,
            "total_amount": total_amount,
            "currency": booking.currency,
            "status": booking.status,
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


CREATE_BOOKING_DRAFT_SCHEMA = {
    "name": "create_booking_draft",
    "description": (
        "Create a draft booking once a customer has chosen a specific tour, "
        "travel date, and number of travelers. Does not require payment yet."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "phone_number": {"type": "string", "description": "Customer's WhatsApp phone number."},
            "tour_id": {"type": "string", "description": "UUID of the tour, from a prior search_tours result."},
            "travel_date": {"type": "string", "description": "Desired travel date, ISO format YYYY-MM-DD."},
            "pax_count": {
                "type": ["integer", "null"],
                "description": "Number of travelers. Pass null to default to 1.",
            },
        },
        "required": ["phone_number", "tour_id", "travel_date", "pax_count"],
        "additionalProperties": False,
    },
}


if __name__ == "__main__":
    # Quick manual test — run with: python -m app.agent.tools.booking
    import json
    from app.agent.tools.search_tours import search_tours

    TEST_PHONE = "+923001234567"  # hardcoded fake test number

    bali = search_tours(destination="Bali")[0]
    print("Booking this tour:", bali["title"])

    result = create_booking_draft(
        phone_number=TEST_PHONE,
        tour_id=bali["id"],
        travel_date="2026-11-20",
        pax_count=2,
    )
    print(json.dumps(result, indent=2))
