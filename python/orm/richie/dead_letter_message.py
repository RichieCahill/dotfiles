"""Dead letter queue for Signal bot messages that fail processing."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from python.orm.richie.base import TableBase
from python.signal_bot.models import MessageStatus


class DeadLetterMessage(TableBase):
    """A Signal message that failed processing and was sent to the dead letter queue."""

    __tablename__ = "dead_letter_message"

    source: Mapped[str]
    message: Mapped[str] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[MessageStatus] = mapped_column(
        ENUM(MessageStatus, name="message_status", create_type=True, schema="main"),
        default=MessageStatus.UNPROCESSED,
    )
