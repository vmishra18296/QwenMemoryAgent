import os
import requests
from typing import Any, Dict, List
from .utils import parse_json_safe


class QwenClient:
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or os.getenv("QWEN_API_KEY")
        self.base_url = base_url or os.getenv("QWEN_API_BASE_URL", "https://api.qwen.cloud/v1")
        self.model = model or os.getenv("QWEN_MODEL", "qwen-plus-1")
        if not self.api_key:
            raise ValueError("Missing QWEN_API_KEY environment variable")

    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def create_chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
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

    def extract_memories(self, user_id: str, user_message: str, conversation_history: str) -> List[Dict[str, Any]]:
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
