"""
Conversation service – manages chat sessions and message persistence.
"""

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.models import Conversation, ConversationStatus, Message, MessageRole
from backend.logging_config import get_logger

logger = get_logger(__name__)

# Maximum messages to include in context window for Gemini
MAX_CONTEXT_MESSAGES = 50


class ConversationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_conversation(
        self,
        tenant_id: uuid.UUID,
        conversation_id: str | None = None,
        end_user_id: uuid.UUID | None = None,
    ) -> Conversation:
        """Get existing conversation or create a new one."""
        if conversation_id:
            try:
                conv_uuid = uuid.UUID(conversation_id)
                result = await self.db.execute(
                    select(Conversation).where(
                        Conversation.id == conv_uuid,
                        Conversation.tenant_id == tenant_id,
                        Conversation.is_active.is_(True),
                    )
                )
                conversation = result.scalar_one_or_none()
                if conversation:
                    return conversation
            except ValueError:
                pass

        # Create new conversation
        conversation = Conversation(
            tenant_id=tenant_id,
            end_user_id=end_user_id,
            title="New Conversation",
        )
        self.db.add(conversation)
        await self.db.flush()

        logger.info(
            "conversation_created",
            tenant_id=str(tenant_id),
            conversation_id=str(conversation.id),
        )
        return conversation

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        role: MessageRole,
        content: str,
        tool_calls: dict | None = None,
    ) -> Message:
        """Add a message to a conversation."""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
        )
        self.db.add(message)

        # Update conversation message count
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            conversation.message_count += 1
            # Auto-title after first exchange
            if conversation.message_count == 1 and role == MessageRole.USER:
                conversation.title = content[:100]

        await self.db.flush()
        return message

    async def get_conversation_history(
        self,
        conversation_id: uuid.UUID,
        limit: int = MAX_CONTEXT_MESSAGES,
    ) -> list[dict]:
        """
        Get conversation history formatted for the Gemini API.
        Returns the most recent messages within the context limit.
        """
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = list(reversed(result.scalars().all()))

        return [
            {
                "role": msg.role.value,
                "content": msg.content,
            }
            for msg in messages
            if msg.role in (MessageRole.USER, MessageRole.ASSISTANT, MessageRole.AGENT)
        ]

    async def get_conversations(
        self,
        tenant_id: uuid.UUID,
        end_user_id: uuid.UUID | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """Get conversations for a tenant/user."""
        conditions = [
            Conversation.tenant_id == tenant_id,
            Conversation.is_active.is_(True),
        ]
        if end_user_id:
            conditions.append(Conversation.end_user_id == end_user_id)

        result = await self.db.execute(
            select(Conversation)
            .where(*conditions)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        conversations = result.scalars().all()

        return [
            {
                "id": str(c.id),
                "title": c.title,
                "message_count": c.message_count,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
            }
            for c in conversations
        ]

    async def get_conversation_with_messages(
        self,
        tenant_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> dict | None:
        """Get a conversation with all its messages."""
        result = await self.db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(
                Conversation.id == conversation_id,
                Conversation.tenant_id == tenant_id,
            )
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            return None

        return {
            "id": str(conversation.id),
            "title": conversation.title,
            "message_count": conversation.message_count,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "messages": [
                {
                    "id": str(m.id),
                    "role": m.role.value,
                    "content": m.content,
                    "created_at": m.created_at.isoformat(),
                }
                for m in conversation.messages
            ],
        }

    async def update_conversation_status(
        self,
        conversation_id: uuid.UUID,
        status: ConversationStatus,
        agent_name: str | None = None,
    ) -> None:
        """Update the handoff status of a conversation."""
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            conversation.status = status
            if agent_name is not None:
                conversation.assigned_agent_name = agent_name
            await self.db.flush()

            logger.info(
                "conversation_status_updated",
                conversation_id=str(conversation_id),
                new_status=status.value,
            )
