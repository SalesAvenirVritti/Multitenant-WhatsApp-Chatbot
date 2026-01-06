import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Text,
    DateTime,
    JSON,
    Integer
)
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base


# -------------------------------------------------
# Tenant
# -------------------------------------------------
class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    api_key = Column(String, unique=True, nullable=False)

    # hospital | restaurant
    domain_type = Column(String, nullable=False)


# -------------------------------------------------
# User
# -------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    phone = Column(String, nullable=False)
    name = Column(String)


# -------------------------------------------------
# Messages (Chat history)
# -------------------------------------------------
class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    direction = Column(String, nullable=False)  # in / out
    message_text = Column(Text, nullable=False)


# -------------------------------------------------
# FAQ
# -------------------------------------------------
class FAQ(Base):
    __tablename__ = "faqs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)


# -------------------------------------------------
# Conversation Session (Memory)
# -------------------------------------------------
class ConversationSession(Base):
    __tablename__ = "conversation_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    state = Column(String, nullable=False)
    context = Column(JSON, nullable=True)

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


# -------------------------------------------------
# Hospital Appointments
# -------------------------------------------------
class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    doctor_name = Column(String, nullable=False)
    appointment_date = Column(String, nullable=False)
    status = Column(String, default="booked")

    created_at = Column(DateTime, default=datetime.utcnow)


# -------------------------------------------------
# Restaurant Menu
# -------------------------------------------------
class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    name = Column(String, nullable=False)
    price = Column(String, nullable=False)
    category = Column(String)


# -------------------------------------------------
# Cart
# -------------------------------------------------
class Cart(Base):
    __tablename__ = "carts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    status = Column(String, default="open")  # open / checked_out


# -------------------------------------------------
# Cart Items
# -------------------------------------------------
class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cart_id = Column(UUID(as_uuid=True), ForeignKey("carts.id"), nullable=False)

    item_name = Column(String, nullable=False)
    size = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
