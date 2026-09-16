"""
Session state persistence.

conversation_sessions is keyed directly by phone_number and is fully
decoupled from the users table (user_id is nullable, optionally set later
if a real booking creates a user). This means the busiest code path — every
single inbound message — only ever touches ONE table, and never creates a
permanent user row just because someone said hi. Only create_booking_draft
(app/db/crud.py get_or_create_user) creates real users.
"""

from app.db.session import SessionLocal
from app.db.models import ConversationSession


def load_history(phone_number: str) -> list[dict] | None:
    """Returns saved message history for this phone number, or None if new."""
    db = SessionLocal()
    try:
        session = db.query(ConversationSession).filter(
            ConversationSession.phone_number == phone_number
        ).first()
        if session is None:
            return None
        context = session.context_data or {}
        return context.get("messages")
    finally:
        db.close()


def save_history(phone_number: str, messages: list[dict]) -> None:
    """Saves message history, creating the session row if it doesn't exist yet."""
    db = SessionLocal()
    try:
        session = db.query(ConversationSession).filter(
            ConversationSession.phone_number == phone_number
        ).first()

        if session is None:
            session = ConversationSession(phone_number=phone_number)
            db.add(session)

        session.context_data = {"messages": messages}
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
