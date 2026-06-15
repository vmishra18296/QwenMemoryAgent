import json
import re
from datetime import datetime, timezone


def normalize_text(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return re.sub(r"\s+", " ", normalized).strip()


def parse_json_safe(text: str):
    try:
        return json.loads(text)
    except Exception:
        cleaned = text.strip()
        json_match = re.search(r"(\[.*\])", cleaned, re.S)
        if json_match:
            return json.loads(json_match.group(1))
        json_match = re.search(r"(\{.*\})", cleaned, re.S)
        return json.loads(json_match.group(1))


def format_timestamp(timestamp: datetime) -> str:
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc).isoformat()
