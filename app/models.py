import enum
import uuid
from sqlalchemy import Column, String, Float, DateTime, Integer, Text, Enum as SAEnum, func
from .db import Base


class MemoryCategory(str, enum.Enum):
    preference = "preference"
    goal = "goal"
    fact = "fact"
    other = "other"


class MemoryEntry(Base):
    __tablename__ = "memories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=False)
    memory_text = Column(Text, nullable=False)
    category = Column(SAEnum(MemoryCategory, name="memory_category"), nullable=False, default=MemoryCategory.other)
    importance_score = Column(Float, nullable=False, default=0.5)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    usage_count = Column(Integer, nullable=False, default=0)


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
