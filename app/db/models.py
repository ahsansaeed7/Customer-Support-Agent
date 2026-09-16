import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    Boolean,
    ForeignKey,
    Text,
    ARRAY,
    CheckConstraint,
    DateTime,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String(20), unique=True, nullable=False)
    full_name = Column(String(100))
    email = Column(String(100))
    passport_number = Column(String(50))
    nationality = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    bookings = relationship("Booking", back_populates="user")
    sessions = relationship("ConversationSession", back_populates="user")
    chat_logs = relationship("ChatLog", back_populates="user")


class Tour(Base):
    __tablename__ = "tours"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(150), nullable=False)
    slug = Column(String(150), unique=True, nullable=False)
    destination = Column(String(100), nullable=False)
    duration_days = Column(Integer, nullable=False)
    base_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    capacity = Column(Integer, nullable=False, default=20)
    available_seats = Column(Integer, nullable=False, default=20)
    is_active = Column(Boolean, default=True)
    tags = Column(ARRAY(Text))
    embedding = Column(Vector(1536))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    itineraries = relationship("Itinerary", back_populates="tour", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="tour")


class Itinerary(Base):
    __tablename__ = "itineraries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tour_id = Column(UUID(as_uuid=True), ForeignKey("tours.id", ondelete="CASCADE"))
    day_number = Column(Integer, nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    activities = Column(ARRAY(Text))
    meal_plan = Column(String(50))
    accommodation = Column(String(100))

    tour = relationship("Tour", back_populates="itineraries")


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','pending_payment','awaiting_human_verification',"
            "'confirmed','cancelled','refunded')",
            name="bookings_status_check",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_reference = Column(String(12), unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    tour_id = Column(UUID(as_uuid=True), ForeignKey("tours.id"))
    travel_date = Column(DateTime(timezone=False), nullable=False)
    pax_count = Column(Integer, nullable=False, default=1)
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String(30), default="draft")
    hold_expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="bookings")
    tour = relationship("Tour", back_populates="bookings")
    payments = relationship("Payment", back_populates="booking", cascade="all, delete-orphan")


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint(
            "payment_method IN ('bank_transfer','stripe','gateway')",
            name="payments_method_check",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"))
    payment_method = Column(String(50))
    transaction_reference = Column(String(100))
    receipt_media_url = Column(Text)
    amount_paid = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    is_verified = Column(Boolean, default=False)
    verified_by_user_id = Column(UUID(as_uuid=True))
    verified_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    booking = relationship("Booking", back_populates="payments")


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    current_state = Column(String(50), default="idle")
    context_data = Column(JSONB, default=dict)
    human_takeover = Column(Boolean, default=False)
    last_interaction_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="sessions")


class ChatLog(Base):
    __tablename__ = "chat_logs"
    __table_args__ = (
        CheckConstraint(
            "sender_type IN ('user','agent_ai','human_agent','system')",
            name="chat_logs_sender_type_check",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    whatsapp_message_id = Column(String(100), unique=True)
    sender_type = Column(String(15))
    message_type = Column(String(20), default="text")
    content = Column(Text)
    media_url = Column(Text)
    raw_payload = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="chat_logs")
