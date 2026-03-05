"""
Chat endpoints – main chat interaction with SSE streaming support.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import AuthContext, get_current_user_optional
from backend.chat.engine import ChatEngine
from backend.db.session import get_db
from backend.schemas import ChatMessageRequest, ChatMessageResponse
from backend.services.conversation_service import ConversationService
from backend.services.faq_service import FAQService
from backend.services.order_service import OrderService
from backend.services.product_service import ProductService
from backend.services.ticket_service import TicketService

router = APIRouter(prefix="/chat", tags=["Chat"])


def _build_chat_engine(
    auth: AuthContext,
    db: AsyncSession,
) -> ChatEngine:
    """Factory to build a ChatEngine with all services wired up."""
    return ChatEngine(
        tenant_id=auth.tenant_id,
        product_service=ProductService(db),
        order_service=OrderService(db),
        faq_service=FAQService(db),
        ticket_service=TicketService(db),
        conversation_service=ConversationService(db),
        system_prompt_override=auth.tenant.system_prompt,
    )


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    body: ChatMessageRequest,
    auth: AuthContext = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a chat message and get a complete response.
    Requires API key. User auth is optional but enables personalized features.
    """
    engine = _build_chat_engine(auth, db)

    result = await engine.chat(
        user_message=body.message,
        conversation_id=body.conversation_id,
        end_user_id=auth.user_id,
    )

    response = ChatMessageResponse(
        conversation_id=result["conversation_id"],
        message_id=result["message_id"],
        content=result["content"],
        role=result["role"],
        timestamp=datetime.fromisoformat(result["timestamp"]) if result.get("timestamp") else datetime.now(timezone.utc),
        handoff=result.get("handoff"),
    )

    return response


@router.post("/stream")
async def stream_message(
    body: ChatMessageRequest,
    auth: AuthContext = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a chat message and receive a streamed response via Server-Sent Events.

    SSE Event Types:
    - conversation_id: Contains the conversation ID
    - chunk: Contains a text chunk of the response
    - done: Signals completion with message_id and conversation_id
    """
    engine = _build_chat_engine(auth, db)

    async def event_generator():
        async for event in engine.chat_stream(
            user_message=body.message,
            conversation_id=body.conversation_id,
            end_user_id=auth.user_id,
        ):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations")
async def list_conversations(
    auth: AuthContext = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """List conversations for the current user/tenant."""
    service = ConversationService(db)
    conversations = await service.get_conversations(
        tenant_id=auth.tenant_id,
        end_user_id=auth.user_id,
    )
    return {"conversations": conversations}


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    auth: AuthContext = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Get a conversation with its messages."""
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID",
        )

    service = ConversationService(db)
    conversation = await service.get_conversation_with_messages(
        tenant_id=auth.tenant_id,
        conversation_id=conv_uuid,
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return conversation
