import os
import re
import requests
from typing import Any, Dict, List
from .utils import parse_json_safe


class QwenClient:
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or os.getenv("QWEN_API_KEY")
        self.base_url = base_url or os.getenv("QWEN_API_BASE_URL", "https://api.qwen.cloud/v1")
        self.model = model or os.getenv("QWEN_MODEL", "qwen-plus-1")
        self.mock = self.api_key is None

    def _headers(self) -> Dict[str, str]:
        if self.mock:
            raise RuntimeError("Mock client does not use headers")
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def create_chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        if self.mock:
            return self._mock_chat_response(messages)

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self._headers(),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        choice = data.get("choices", [])[0]
        content = choice.get("message", {}).get("content") or choice.get("text")
        if content is None:
            raise ValueError("No content returned from Qwen API")
        return content.strip()

    def _mock_chat_response(self, messages: List[Dict[str, str]]) -> str:
        user_message = ""
        for message in reversed(messages):
            if message.get("role") == "user":
                user_message = message.get("content", "")
                break
        if "memory" in user_message.lower() or "remember" in user_message.lower():
            return "I will keep that in mind for future conversations."
        return "This is a mock QwenMemoryAgent response. Set QWEN_API_KEY in .env for real Qwen API behavior."

    def extract_memories(self, user_id: str, user_message: str, conversation_history: str) -> List[Dict[str, Any]]:
        if self.mock:
            return self._mock_extract_memories(user_message)

        prompt = (
            "You are a memory extraction assistant.\n"
            "Extract only long-term, meaningful user memories from the conversation. "
            "Do not store small talk or temporary details. "
            "Output valid JSON array of objects with keys: memory_text, category, importance_score. "
            "Categories must be one of preference, goal, fact, other.\n\n"
            f"Conversation history:\n{conversation_history}\n\n"
            f"Latest user message:\n{user_message}\n\n"
            "Return only JSON."
        )
        messages = [
            {"role": "system", "content": "You extract long-term user memories for a persistent agent."},
            {"role": "user", "content": prompt},
        ]
        raw = self.create_chat_completion(messages, temperature=0.3)
        parsed = parse_json_safe(raw)
        if isinstance(parsed, dict):
            parsed = [parsed]
        if not isinstance(parsed, list):
            raise ValueError("Memory extraction response is not a list")
        memories = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            memory_text = item.get("memory_text")
            category = item.get("category")
            importance = float(item.get("importance_score", 0.4))
            if memory_text:
                memories.append({
                    "memory_text": memory_text.strip(),
                    "category": category if category in ["preference", "goal", "fact", "other"] else "other",
                    "importance_score": max(0.1, min(1.0, importance)),
                })
        return memories

    def _mock_extract_memories(self, user_message: str) -> List[Dict[str, Any]]:
        text = user_message.lower()
        memories = []
        if "i like" in text or "i love" in text or "i prefer" in text:
            preference = re.findall(r"i (?:like|love|prefer) ([^.?!]+)", text)
            if preference:
                memories.append({
                    "memory_text": f"User likes {preference[0].strip()}",
                    "category": "preference",
                    "importance_score": 0.7,
                })
        if "my goal" in text or "i want to" in text or "i'm trying to" in text:
            memories.append({
                "memory_text": user_message.strip(),
                "category": "goal",
                "importance_score": 0.8,
            })
        if "working on" in text or "startup" in text or "project" in text:
            memories.append({
                "memory_text": user_message.strip(),
                "category": "fact",
                "importance_score": 0.6,
            })
        return memories
