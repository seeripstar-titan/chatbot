"""
SQLAlchemy ORM models for the chatbot application.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base model with common fields."""

    type_annotation_map = {
        dict: JSON,
    }


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ── Enums ────────────────────────────────────────────────────────────────────


class TenantStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
    AGENT = "agent"


class ConversationStatus(str, enum.Enum):
    BOT = "bot"
    QUEUED = "queued"
    AGENT_CONNECTED = "agent_connected"
    AGENT_CLOSED = "agent_closed"


# ── Tenant (Multi-tenant support) ───────────────────────────────────────────


class Tenant(Base, TimestampMixin):
    """
    Represents a customer/company that embeds the chatbot on their website.
    Each tenant gets their own API key and configuration.
    """

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    status: Mapped[TenantStatus] = mapped_column(
        Enum(TenantStatus), default=TenantStatus.TRIAL, nullable=False
    )
    settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    # Bot personality / system prompt override
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    welcome_message: Mapped[str] = mapped_column(
        Text, default="Hello! How can I help you today?"
    )
    max_conversations_per_day: Mapped[int] = mapped_column(Integer, default=1000)

    # Relationships
    api_keys: Mapped[list["APIKey"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    products: Mapped[list["Product"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    faqs: Mapped[list["FAQ"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_tenants_domain", "domain"),
        Index("ix_tenants_status", "status"),
    )


# ── API Key ──────────────────────────────────────────────────────────────────


class APIKey(Base, TimestampMixin):
    """API keys for authenticating widget requests."""

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    key_prefix: Mapped[str] = mapped_column(String(12), nullable=False)  # First 8 chars for identification
    name: Mapped[str] = mapped_column(String(255), default="Default Key")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allowed_origins: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="api_keys")


# ── End User ─────────────────────────────────────────────────────────────────


class EndUser(Base, TimestampMixin):
    """
    End users who interact with the chatbot.
    Can be authenticated (email-verified) or anonymous.
    """

    __tablename__ = "end_users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)

    conversations: Mapped[list["Conversation"]] = relationship(back_populates="end_user")

    __table_args__ = (
        Index("ix_end_users_tenant_email", "tenant_id", "email", unique=True),
    )


# ── Product ──────────────────────────────────────────────────────────────────


class Product(Base, TimestampMixin):
    """Product catalog for product inquiry support."""

    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    sku: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    specifications: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="products")

    __table_args__ = (
        Index("ix_products_tenant_sku", "tenant_id", "sku", unique=True),
        Index("ix_products_tenant_category", "tenant_id", "category"),
        Index("ix_products_name", "name"),
    )


# ── Order ────────────────────────────────────────────────────────────────────


class Order(Base, TimestampMixin):
    """Order records for order tracking."""

    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    order_number: Mapped[str] = mapped_column(String(100), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False
    )
    items: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    shipping_address: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    tracking_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    carrier: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estimated_delivery: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="orders")

    __table_args__ = (
        Index("ix_orders_tenant_number", "tenant_id", "order_number", unique=True),
        Index("ix_orders_customer_email", "tenant_id", "customer_email"),
        Index("ix_orders_status", "status"),
    )


# ── FAQ ──────────────────────────────────────────────────────────────────────


class FAQ(Base, TimestampMixin):
    """Frequently asked questions knowledge base."""

    __tablename__ = "faqs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(255), default="general")
    keywords: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0)

    tenant: Mapped["Tenant"] = relationship(back_populates="faqs")

    __table_args__ = (
        Index("ix_faqs_tenant_category", "tenant_id", "category"),
    )


# ── Support Ticket ───────────────────────────────────────────────────────────


class SupportTicket(Base, TimestampMixin):
    """Customer support tickets created via chatbot."""

    __tablename__ = "support_tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    ticket_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("conversations.id"), nullable=True
    )
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus), default=TicketStatus.OPEN, nullable=False
    )
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority), default=TicketPriority.MEDIUM, nullable=False
    )
    category: Mapped[str] = mapped_column(String(255), default="general")

    __table_args__ = (
        Index("ix_tickets_tenant_status", "tenant_id", "status"),
        Index("ix_tickets_customer_email", "customer_email"),
    )


# ── Conversation & Messages ─────────────────────────────────────────────────


class Conversation(Base, TimestampMixin):
    """A chat conversation session."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    end_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("end_users.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), default="New Conversation")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus), default=ConversationStatus.BOT, nullable=False,
        name="conv_status",
    )
    assigned_agent_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    message_count: Mapped[int] = mapped_column(Integer, default=0)

    tenant: Mapped["Tenant"] = relationship(back_populates="conversations")
    end_user: Mapped["EndUser | None"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at"
    )

    __table_args__ = (
        Index("ix_conversations_tenant", "tenant_id"),
        Index("ix_conversations_end_user", "end_user_id"),
    )


class Message(Base, TimestampMixin):
    """Individual messages within a conversation."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_calls: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

    __table_args__ = (
        Index("ix_messages_conversation", "conversation_id"),
        Index("ix_messages_created_at", "created_at"),
    )
