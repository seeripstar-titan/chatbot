"""
Agent service – manages WebSocket connections and live agent handoff.

Uses an in-memory connection manager for message relay between
end-users and support agents over the same conversation.
"""

import json
import uuid
from datetime import datetime, timezone

from fastapi import WebSocket

from backend.logging_config import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """
    Manages active WebSocket connections for live agent chat.

    Tracks two sides per conversation:
      - "user"  → the end-user's WebSocket
      - "agent" → the support agent's WebSocket

    Messages sent by one side are relayed to the other side in real time,
    while also being persisted via ConversationService by the caller.
    """

    def __init__(self):
        # conversation_id (str) → {"user": WebSocket | None, "agent": WebSocket | None}
        self._connections: dict[str, dict[str, WebSocket | None]] = {}
        # conversation_id → list of queued messages while the other party is not connected
        self._pending: dict[str, list[dict]] = {}

    # ── Connection lifecycle ─────────────────────────────────────────────

    async def connect_user(self, conversation_id: str, ws: WebSocket):
        """Register end-user WebSocket for a conversation."""
        await ws.accept()
        self._ensure_slot(conversation_id)
        self._connections[conversation_id]["user"] = ws
        logger.info("ws_user_connected", conversation_id=conversation_id)

        # Flush any pending messages from agent
        await self._flush_pending(conversation_id, target="user", ws=ws)

    async def connect_agent(self, conversation_id: str, ws: WebSocket):
        """Register agent WebSocket for a conversation."""
        await ws.accept()
        self._ensure_slot(conversation_id)
        self._connections[conversation_id]["agent"] = ws
        logger.info("ws_agent_connected", conversation_id=conversation_id)

        # Notify user that an agent has connected
        user_ws = self._connections[conversation_id].get("user")
        if user_ws:
            await self._safe_send(user_ws, {
                "type": "agent_joined",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        # Flush any pending messages from user
        await self._flush_pending(conversation_id, target="agent", ws=ws)

    def disconnect_user(self, conversation_id: str):
        """Remove end-user WebSocket."""
        if conversation_id in self._connections:
            self._connections[conversation_id]["user"] = None
            self._cleanup_if_empty(conversation_id)
        logger.info("ws_user_disconnected", conversation_id=conversation_id)

    def disconnect_agent(self, conversation_id: str):
        """Remove agent WebSocket."""
        if conversation_id in self._connections:
            self._connections[conversation_id]["agent"] = None
            self._cleanup_if_empty(conversation_id)
        logger.info("ws_agent_disconnected", conversation_id=conversation_id)

    # ── Message relay ────────────────────────────────────────────────────

    async def relay_to_agent(self, conversation_id: str, message: dict):
        """Send a message from the user to the agent."""
        agent_ws = self._get_ws(conversation_id, "agent")
        if agent_ws:
            await self._safe_send(agent_ws, message)
        else:
            # Queue for when agent connects
            self._pending.setdefault(conversation_id, []).append(
                {"target": "agent", **message}
            )

    async def relay_to_user(self, conversation_id: str, message: dict):
        """Send a message from the agent to the user."""
        user_ws = self._get_ws(conversation_id, "user")
        if user_ws:
            await self._safe_send(user_ws, message)
        else:
            self._pending.setdefault(conversation_id, []).append(
                {"target": "user", **message}
            )

    async def notify_agent_closed(self, conversation_id: str):
        """Notify the user that the agent has ended the session."""
        user_ws = self._get_ws(conversation_id, "user")
        if user_ws:
            await self._safe_send(user_ws, {
                "type": "agent_left",
                "message": "The agent has ended the live chat. You're now back with the AI assistant.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    # ── Queue management ─────────────────────────────────────────────────

    def get_queued_conversations(self) -> list[str]:
        """Return conversation IDs that have a user connected but no agent."""
        queued = []
        for conv_id, sockets in self._connections.items():
            if sockets.get("user") and not sockets.get("agent"):
                queued.append(conv_id)
        return queued

    def is_agent_connected(self, conversation_id: str) -> bool:
        """Check if an agent is connected to a conversation."""
        return bool(self._get_ws(conversation_id, "agent"))

    def is_user_connected(self, conversation_id: str) -> bool:
        """Check if a user is connected to a conversation."""
        return bool(self._get_ws(conversation_id, "user"))

    # ── Internal helpers ─────────────────────────────────────────────────

    def _ensure_slot(self, conversation_id: str):
        if conversation_id not in self._connections:
            self._connections[conversation_id] = {"user": None, "agent": None}

    def _get_ws(self, conversation_id: str, role: str) -> WebSocket | None:
        return self._connections.get(conversation_id, {}).get(role)

    def _cleanup_if_empty(self, conversation_id: str):
        slot = self._connections.get(conversation_id)
        if slot and not slot.get("user") and not slot.get("agent"):
            del self._connections[conversation_id]
            self._pending.pop(conversation_id, None)

    async def _flush_pending(self, conversation_id: str, target: str, ws: WebSocket):
        pending = self._pending.get(conversation_id, [])
        remaining = []
        for msg in pending:
            if msg.get("target") == target:
                payload = {k: v for k, v in msg.items() if k != "target"}
                await self._safe_send(ws, payload)
            else:
                remaining.append(msg)
        if remaining:
            self._pending[conversation_id] = remaining
        elif conversation_id in self._pending:
            del self._pending[conversation_id]

    @staticmethod
    async def _safe_send(ws: WebSocket, data: dict):
        try:
            await ws.send_json(data)
        except Exception:
            pass  # Connection may have been closed


# Global singleton — shared across the app
manager = ConnectionManager()
