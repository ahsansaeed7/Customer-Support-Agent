"""
confirm_booking_intent tool.

Called when a customer verbally confirms they want to proceed with a draft
booking. Moves status from 'draft' -> 'pending_payment' — NOT 'confirmed'.
Per the original architecture spec, 'confirmed' only happens after a human
verifies payment; this tool is the customer-facing "yes, go ahead" step.
"""

from app.db.session import SessionLocal
from app.db.models import Booking


def confirm_booking_intent(booking_id: str) -> dict:
    """
    Moves a booking from 'draft' to 'pending_payment'.
    Returns an error if the booking doesn't exist or isn't in 'draft' status
    (e.g. already confirmed, cancelled — customer shouldn't be able to
    re-confirm something that's already moved on).
    """
    db = SessionLocal()
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if booking is None:
            return {"error": "Booking not found."}

        if booking.status != "draft":
            return {"error": f"Booking is already in status '{booking.status}', cannot re-confirm."}

        booking.status = "pending_payment"
        db.commit()
        db.refresh(booking)

        return {
            "booking_id": str(booking.id),
            "booking_reference": booking.booking_reference,
            "status": booking.status,
            "total_amount": float(booking.total_amount),
            "currency": booking.currency,
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


CONFIRM_BOOKING_INTENT_SCHEMA = {
    "name": "confirm_booking_intent",
    "description": (
        "Call this when a customer verbally confirms they want to proceed "
        "with an existing draft booking (e.g. says 'yes', 'confirm it', "
        "'let's go ahead'). This moves the booking to pending_payment status "
        "so payment instructions can be shared. Never claim a booking is "
        "confirmed or moved forward without calling this tool first — your "
        "own words don't change anything in the system."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "booking_id": {
                "type": "string",
                "description": "UUID of the booking, from a prior create_booking_draft result.",
            },
        },
        "required": ["booking_id"],
        "additionalProperties": False,
    },
}
