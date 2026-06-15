import math
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .models import MemoryEntry, ConversationMessage, MemoryCategory
from .utils import normalize_text


class MemoryManager:
    def __init__(self, db: Session, qwen_client):
        self.db = db
        self.qwen_client = qwen_client

    def add_conversation_message(self, user_id: str, role: str, content: str) -> None:
        message = ConversationMessage(user_id=user_id, role=role, content=content)
        self.db.add(message)
        self.db.commit()

    def get_conversation_history(self, user_id: str, limit: int = 10):
        rows = (
            self.db.query(ConversationMessage)
            .filter(ConversationMessage.user_id == user_id)
            .order_by(ConversationMessage.timestamp.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(rows))

    def extract_and_store_memories(self, user_id: str, user_message: str, conversation_history: str):
        extracted = self.qwen_client.extract_memories(user_id, user_message, conversation_history)
        stored = []
        for item in extracted:
            memory_text = item["memory_text"].strip()
            if not self._should_store(memory_text):
                continue
            raw_category = item.get("category", "other")
            try:
                category = MemoryCategory(raw_category)
            except ValueError:
                category = MemoryCategory.other
            score = float(item.get("importance_score", 0.4))
            entry = self.update_or_create_memory(user_id, memory_text, category, score)
            if entry is not None:
                stored.append(entry)
        return stored

    def _should_store(self, memory_text: str) -> bool:
        if len(memory_text) < 20:
            return False
        lower_text = memory_text.lower()
        if any(token in lower_text for token in ["okay", "thanks", "bye", "hello", "sure", "yes", "no"]):
            return False
        return True

    def update_or_create_memory(self, user_id: str, memory_text: str, category: MemoryCategory, importance_score: float):
        existing = (
            self.db.query(MemoryEntry)
            .filter(MemoryEntry.user_id == user_id, MemoryEntry.memory_text == memory_text)
            .first()
        )
        now = datetime.utcnow()
        if existing:
            existing.importance_score = min(1.0, max(existing.importance_score, importance_score) + 0.05)
            existing.category = category
            existing.last_used_at = now
            existing.usage_count += 1
            self.db.add(existing)
            self.db.commit()
            return existing
        new_memory = MemoryEntry(
            user_id=user_id,
            memory_text=memory_text,
            category=category,
            importance_score=importance_score,
            last_used_at=now,
            usage_count=1,
        )
        self.db.add(new_memory)
        self.db.commit()
        return new_memory

    def retrieve_relevant_memories(self, user_id: str, query: str, top_k: int = 5):
        now = datetime.utcnow()
        query_tokens = set(normalize_text(query).split())
        results = []
        for memory in self.db.query(MemoryEntry).filter(MemoryEntry.user_id == user_id).all():
            memory_tokens = set(normalize_text(memory.memory_text).split())
            overlap = len(query_tokens.intersection(memory_tokens))
            relevance = overlap / max(len(memory_tokens), 1)
            age_days = max((now - memory.timestamp).total_seconds() / 86400.0, 0.0)
            recency_weight = math.exp(-0.08 * age_days)
            score = importance_score = memory.importance_score * 1.0
            score += relevance * 1.5 + recency_weight * 0.6
            if relevance > 0.0 or importance_score > 0.5:
                results.append((score, memory))
        results.sort(key=lambda pair: pair[0], reverse=True)
        selected = [entry for _, entry in results[:top_k]]
        for memory in selected:
            memory.usage_count += 1
            memory.last_used_at = now
            memory.importance_score = min(1.0, memory.importance_score + 0.03)
            self.db.add(memory)
        self.db.commit()
        return selected

    def decay_memories(self, user_id: str, decay_lambda: float = 0.01, delete_threshold: float = 0.15):
        now = datetime.utcnow()
        entries = self.db.query(MemoryEntry).filter(MemoryEntry.user_id == user_id).all()
        for entry in entries:
            age_days = max((now - entry.last_used_at).total_seconds() / 86400.0, 0.0)
            entry.importance_score = max(0.05, entry.importance_score * math.exp(-decay_lambda * age_days))
            if entry.importance_score < delete_threshold and age_days > 60:
                self.db.delete(entry)
            else:
                self.db.add(entry)
        self.db.commit()

    def get_memories(self, user_id: str):
        return (
            self.db.query(MemoryEntry)
            .filter(MemoryEntry.user_id == user_id)
            .order_by(MemoryEntry.importance_score.desc(), MemoryEntry.timestamp.desc())
            .all()
        )

    def clear_memory(self, user_id: str):
        self.db.query(MemoryEntry).filter(MemoryEntry.user_id == user_id).delete()
        self.db.query(ConversationMessage).filter(ConversationMessage.user_id == user_id).delete()
        self.db.commit()
