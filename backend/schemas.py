"""
Pydantic schemas for request/response validation.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ── Auth Schemas ─────────────────────────────────────────────────────────────


class UserRegisterRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ── Chat Schemas ─────────────────────────────────────────────────────────────


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: str | None = None


class HandoffInfo(BaseModel):
    status: str
    reason: str


class ChatMessageResponse(BaseModel):
    conversation_id: str
    message_id: str
    content: str
    role: str = "assistant"
    timestamp: datetime
    handoff: HandoffInfo | None = None


class ConversationResponse(BaseModel):
    id: str
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class ConversationDetailResponse(ConversationResponse):
    messages: list["MessageResponse"]


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime


# ── Product Schemas ──────────────────────────────────────────────────────────


class ProductResponse(BaseModel):
    id: str
    sku: str
    name: str
    description: str
    category: str
    price: float
    currency: str
    in_stock: bool
    stock_quantity: int
    specifications: dict
    image_url: str | None


class ProductSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    category: str | None = None
    min_price: float | None = None
    max_price: float | None = None


# ── Order Schemas ────────────────────────────────────────────────────────────


class OrderTrackRequest(BaseModel):
    order_number: str = Field(..., min_length=1, max_length=100)
    email: EmailStr


class OrderResponse(BaseModel):
    order_number: str
    status: str
    items: list
    total_amount: float
    currency: str
    tracking_number: str | None
    carrier: str | None
    estimated_delivery: datetime | None
    shipped_at: datetime | None
    delivered_at: datetime | None
    created_at: datetime


# ── Support Ticket Schemas ───────────────────────────────────────────────────


class CreateTicketRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1, max_length=5000)
    category: str = "general"
    customer_email: EmailStr
    customer_name: str = Field(..., min_length=1, max_length=255)


class TicketResponse(BaseModel):
    ticket_number: str
    subject: str
    status: str
    priority: str
    category: str
    created_at: datetime


# ── Tenant Admin Schemas ────────────────────────────────────────────────────


class TenantCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., min_length=1, max_length=255)
    system_prompt: str | None = None
    welcome_message: str = "Hello! How can I help you today?"


class TenantResponse(BaseModel):
    id: str
    name: str
    domain: str
    status: str
    welcome_message: str
    created_at: datetime


class APIKeyCreateResponse(BaseModel):
    api_key: str  # Raw key, shown only once
    key_prefix: str
    name: str
    message: str = "Store this API key securely. It will not be shown again."


# ── Health Check ─────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    environment: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None
    request_id: str | None = None
