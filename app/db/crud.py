from sqlalchemy.orm import Session
from app.db.models import Tour, User


def get_or_create_user(db: Session, phone_number: str) -> User:
    """
    Find a user by phone number, or create one on the spot.
    Called only when a customer actually commits to a booking —
    not on every inbound message.
    """
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if user:
        return user

    user = User(phone_number=phone_number)
    db.add(user)
    db.flush()  # get user.id without committing yet
    return user


def query_tours(
    db: Session,
    destination: str | None = None,
    max_budget: float | None = None,
    duration: int | None = None,
    limit: int = 5,
) -> list[Tour]:
    """
    Filter active tours by optional destination substring, max budget, and duration.
    Returns SQLAlchemy Tour objects.
    """
    q = db.query(Tour).filter(Tour.is_active.is_(True))

    if destination:
        # case-insensitive partial match, e.g. "bali" matches "Bali, Indonesia"
        q = q.filter(Tour.destination.ilike(f"%{destination}%"))

    if max_budget is not None:
        q = q.filter(Tour.base_price <= max_budget)

    if duration is not None:
        q = q.filter(Tour.duration_days == duration)

    return q.order_by(Tour.base_price.asc()).limit(limit).all()


def get_tour_by_id(db: Session, tour_id: str) -> Tour | None:
    return db.query(Tour).filter(Tour.id == tour_id).first()
