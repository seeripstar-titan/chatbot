"""
Agent endpoints – WebSocket routes for live agent handoff and an agent dashboard API.

Two WebSocket endpoints:
  /ws/chat/{conversation_id}   – end-user side
  /ws/agent/{conversation_id}  – support agent side

REST endpoints for the agent dashboard:
  GET  /agent/queue             – list conversations waiting for an agent
  POST /agent/close/{conv_id}  – agent closes the live session (returns to bot)
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.api_keys import hash_api_key
from backend.db.models import (
    APIKey,
    Conversation,
    ConversationStatus,
    Message,
    MessageRole,
    Tenant,
)
from backend.db.session import get_async_session, get_db
from backend.logging_config import get_logger
from backend.services.agent_service import manager
from backend.services.conversation_service import ConversationService

logger = get_logger(__name__)

router = APIRouter(tags=["Agent"])


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _validate_api_key_raw(api_key: str, db: AsyncSession) -> Tenant | None:
    """Validate an API key string and return the tenant (used in WS flows)."""
    key_hash = hash_api_key(api_key)
    result = await db.execute(
        select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active.is_(True))
    )
    ak = result.scalar_one_or_none()
    if not ak:
        return None
    result = await db.execute(select(Tenant).where(Tenant.id == ak.tenant_id))
    return result.scalar_one_or_none()


# ── WebSocket: End-User side ─────────────────────────────────────────────────


@router.websocket("/ws/chat/{conversation_id}")
async def ws_user_chat(
    ws: WebSocket,
    conversation_id: str,
    api_key: str = Query(..., alias="api_key"),
):
    """
    WebSocket for the end-user during a live agent session.

    After the AI triggers a handoff, the widget opens this WebSocket.
    Messages from the user are relayed to the connected agent, and vice-versa.
    """
    async with get_async_session() as db:
        tenant = await _validate_api_key_raw(api_key, db)
        if not tenant:
            await ws.close(code=4001, reason="Invalid API key")
            return

        # Verify conversation exists and belongs to tenant
        try:
            conv_uuid = uuid.UUID(conversation_id)
        except ValueError:
            await ws.close(code=4002, reason="Invalid conversation ID")
            return

        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conv_uuid,
                Conversation.tenant_id == tenant.id,
            )
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            await ws.close(code=4003, reason="Conversation not found")
            return

    # Connect
    await manager.connect_user(conversation_id, ws)

    try:
        while True:
            data = await ws.receive_json()
            message_text = data.get("message", "").strip()
            if not message_text:
                continue

            # Persist the user message
            async with get_async_session() as db:
                service = ConversationService(db)
                await service.add_message(
                    conversation_id=conv_uuid,
                    role=MessageRole.USER,
                    content=message_text,
                )
                await db.commit()

            # Relay to agent
            await manager.relay_to_agent(conversation_id, {
                "type": "message",
                "role": "user",
                "content": message_text,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    except WebSocketDisconnect:
        manager.disconnect_user(conversation_id)
    except Exception as e:
        logger.error("ws_user_error", error=str(e), conversation_id=conversation_id)
        manager.disconnect_user(conversation_id)


# ── WebSocket: Agent side ────────────────────────────────────────────────────


@router.websocket("/ws/agent/{conversation_id}")
async def ws_agent_chat(
    ws: WebSocket,
    conversation_id: str,
    agent_name: str = Query("Support Agent"),
):
    """
    WebSocket for the support agent.

    The agent dashboard opens this connection to chat with the end-user.
    Messages from the agent are relayed to the user and persisted with AGENT role.
    """
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        await ws.close(code=4002, reason="Invalid conversation ID")
        return

    # Update conversation status to agent_connected
    async with get_async_session() as db:
        result = await db.execute(
            select(Conversation).where(Conversation.id == conv_uuid)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            await ws.close(code=4003, reason="Conversation not found")
            return

        conversation.status = ConversationStatus.AGENT_CONNECTED
        conversation.assigned_agent_name = agent_name
        await db.commit()

    await manager.connect_agent(conversation_id, ws)

    try:
        while True:
            data = await ws.receive_json()
            message_text = data.get("message", "").strip()
            if not message_text:
                continue

            # Persist the agent message
            async with get_async_session() as db:
                service = ConversationService(db)
                await service.add_message(
                    conversation_id=conv_uuid,
                    role=MessageRole.AGENT,
                    content=message_text,
                )
                await db.commit()

            # Relay to user
            await manager.relay_to_user(conversation_id, {
                "type": "message",
                "role": "agent",
                "content": message_text,
                "agent_name": agent_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    except WebSocketDisconnect:
        manager.disconnect_agent(conversation_id)
        # Notify user the agent left
        await manager.notify_agent_closed(conversation_id)
        # Update status back
        async with get_async_session() as db:
            result = await db.execute(
                select(Conversation).where(Conversation.id == conv_uuid)
            )
            conv = result.scalar_one_or_none()
            if conv:
                conv.status = ConversationStatus.BOT
                conv.assigned_agent_name = None
                await db.commit()

    except Exception as e:
        logger.error("ws_agent_error", error=str(e), conversation_id=conversation_id)
        manager.disconnect_agent(conversation_id)


# ── REST: Agent Dashboard API ────────────────────────────────────────────────


@router.get("/agent/queue")
async def get_agent_queue(
    db: AsyncSession = Depends(get_db),
):
    """
    List conversations that are waiting for (or connected to) a live agent.
    Used by the agent dashboard to show the queue.
    """
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.status.in_([
                ConversationStatus.QUEUED,
                ConversationStatus.AGENT_CONNECTED,
            ]),
            Conversation.is_active.is_(True),
        )
        .order_by(Conversation.updated_at.desc())
    )
    conversations = result.scalars().all()

    queue = []
    for conv in conversations:
        # Get last few messages for context
        msg_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at.desc())
            .limit(5)
        )
        recent_messages = list(reversed(msg_result.scalars().all()))

        queue.append({
            "id": str(conv.id),
            "title": conv.title,
            "status": conv.status.value,
            "assigned_agent": conv.assigned_agent_name,
            "message_count": conv.message_count,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat(),
            "recent_messages": [
                {
                    "role": m.role.value,
                    "content": m.content,
                    "created_at": m.created_at.isoformat(),
                }
                for m in recent_messages
            ],
        })

    return {"queue": queue}


@router.post("/agent/close/{conversation_id}")
async def close_agent_session(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Agent closes the live session. Conversation returns to bot mode.
    """
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID",
        )

    result = await db.execute(
        select(Conversation).where(Conversation.id == conv_uuid)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    conversation.status = ConversationStatus.BOT
    conversation.assigned_agent_name = None
    await db.commit()

    # Notify user via WebSocket
    await manager.notify_agent_closed(conversation_id)
    manager.disconnect_agent(conversation_id)

    return {"status": "closed", "conversation_id": conversation_id}


@router.get("/agent/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get full message history for a conversation (used by agent dashboard)."""
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID",
        )

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv_uuid)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()

    return {
        "messages": [
            {
                "id": str(m.id),
                "role": m.role.value,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ]
    }
