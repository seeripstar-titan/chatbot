"""
Tests for Pydantic schemas and validation.
"""

import pytest
from pydantic import ValidationError

from backend.schemas import (
    ChatMessageRequest,
    UserLoginRequest,
    UserRegisterRequest,
    OrderTrackRequest,
    CreateTicketRequest,
    TenantCreateRequest,
)


class TestChatMessageRequest:
    def test_valid_message(self):
        msg = ChatMessageRequest(message="Hello, how are you?")
        assert msg.message == "Hello, how are you?"
        assert msg.conversation_id is None

    def test_with_conversation_id(self):
        msg = ChatMessageRequest(
            message="Follow up",
            conversation_id="abc-123",
        )
        assert msg.conversation_id == "abc-123"

    def test_empty_message_rejected(self):
        with pytest.raises(ValidationError):
            ChatMessageRequest(message="")

    def test_message_too_long(self):
        with pytest.raises(ValidationError):
            ChatMessageRequest(message="x" * 5001)


class TestUserRegisterRequest:
    def test_valid_registration(self):
        req = UserRegisterRequest(
            email="test@example.com",
            name="John Doe",
            password="securePass123",
        )
        assert req.email == "test@example.com"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                email="not-an-email",
                name="John",
                password="securePass123",
            )

    def test_short_password(self):
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                email="test@example.com",
                name="John",
                password="short",
            )


class TestOrderTrackRequest:
    def test_valid_request(self):
        req = OrderTrackRequest(
            order_number="ORD-001",
            email="john@example.com",
        )
        assert req.order_number == "ORD-001"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            OrderTrackRequest(order_number="ORD-001", email="invalid")


class TestTenantCreateRequest:
    def test_valid_tenant(self):
        req = TenantCreateRequest(
            name="My Store",
            domain="mystore.com",
        )
        assert req.name == "My Store"
        assert req.welcome_message == "Hello! How can I help you today?"

    def test_custom_welcome(self):
        req = TenantCreateRequest(
            name="My Store",
            domain="mystore.com",
            welcome_message="Hi there!",
        )
        assert req.welcome_message == "Hi there!"
