"""add conversation status and agent handoff fields

Revision ID: 20260305_agent_handoff
Revises:
Create Date: 2026-03-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260305_agent_handoff"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Enum values
conversation_status_values = ("bot", "queued", "agent_connected", "agent_closed")
message_role_values = ("user", "assistant", "system", "tool", "agent")


def upgrade() -> None:
    # Create the conversation status enum type
    conv_status_enum = sa.Enum(
        *conversation_status_values, name="conversationstatus"
    )

    # Add new columns to conversations table
    op.add_column(
        "conversations",
        sa.Column(
            "conv_status",
            conv_status_enum,
            nullable=False,
            server_default="bot",
        ),
    )
    op.add_column(
        "conversations",
        sa.Column("assigned_agent_name", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("conversations", "assigned_agent_name")
    op.drop_column("conversations", "conv_status")
    # Drop the enum type if using PostgreSQL
    sa.Enum(name="conversationstatus").drop(op.get_bind(), checkfirst=True)
