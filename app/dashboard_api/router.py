"""
HITL dashboard backend endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.db.session import SessionLocal
from app.db.models import Booking, User, Tour
from app.whatsapp.client import send_text

router = APIRouter(prefix="/dashboard")


class BookingOut(BaseModel):
    id: str
    booking_reference: str
    status: str
    phone_number: str
    tour_title: str
    travel_date: str
    pax_count: int
    total_amount: float
    currency: str

    class Config:
        from_attributes = True


@router.get("/bookings", response_model=list[BookingOut])
def list_bookings(status: str | None = Query(default=None)):
    db = SessionLocal()
    try:
        q = db.query(Booking).join(User).join(Tour)
        if status:
            q = q.filter(Booking.status == status)
        bookings = q.order_by(Booking.created_at.desc()).all()

        return [
            BookingOut(
                id=str(b.id),
                booking_reference=b.booking_reference,
                status=b.status,
                phone_number=b.user.phone_number,
                tour_title=b.tour.title,
                travel_date=str(b.travel_date),
                pax_count=b.pax_count,
                total_amount=float(b.total_amount),
                currency=b.currency,
            )
            for b in bookings
        ]
    finally:
        db.close()


@router.post("/bookings/{booking_id}/approve")
def approve_booking(booking_id: str):
    """
    Human agent approves a pending_payment booking -> confirmed.
    Also notifies the customer on WhatsApp — this is the step that was
    missing before: flipping the DB status alone tells the customer nothing.
    """
    db = SessionLocal()
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if booking is None:
            raise HTTPException(status_code=404, detail="Booking not found.")
        if booking.status != "pending_payment":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot approve a booking in status '{booking.status}'.",
            )

        booking.status = "confirmed"
        db.commit()

        customer_phone = booking.user.phone_number
        tour_title = booking.tour.title

        try:
            send_text(
                to=customer_phone,
                body=(
                    f"🎉 Great news! Your booking *{booking.booking_reference}* for "
                    f"*{tour_title}* has been confirmed. Payment received — "
                    f"we look forward to having you on the trip!"
                ),
            )
            notified = True
        except Exception:
            # Don't fail the whole approval if WhatsApp delivery has an
            # issue — the booking IS confirmed in the DB either way. Just
            # let the dashboard know the notification itself didn't go out
            # so the human agent can follow up manually.
            notified = False

        return {"booking_id": booking_id, "status": "confirmed", "customer_notified": notified}
    finally:
        db.close()
