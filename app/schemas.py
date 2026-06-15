from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class MemoryCategory(str, Enum):
    preference = "preference"
    goal = "goal"
    fact = "fact"
    other = "other"


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ResetMemoryRequest(BaseModel):
    user_id: str


class MemoryOut(BaseModel):
    id: str
    user_id: str
    memory_text: str
    category: MemoryCategory
    importance_score: float
    timestamp: datetime

    class Config:
        orm_mode = True


class ChatResponse(BaseModel):
    response: str
    retrieved_memories: List[MemoryOut]
    debug: Optional[str] = None
