import os
from pathlib import Path
from typing import List
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from .db import init_db, SessionLocal
from .memory_manager import MemoryManager
from .qwen_client import QwenClient
from .schemas import ChatRequest, ChatResponse, MemoryOut, ResetMemoryRequest

load_dotenv()

app = FastAPI(
    title="QwenMemoryAgent",
    description="A FastAPI backend for a memory-augmented Qwen assistant.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=Path(__file__).resolve().parent.parent / "static"), name="static")

QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-plus-1")
qwen_client = None


def get_qwen_client() -> QwenClient:
    global qwen_client
    if qwen_client is None:
        api_key = os.getenv("QWEN_API_KEY")
        base_url = os.getenv("QWEN_API_BASE_URL")
        if not api_key:
            raise ValueError("Missing QWEN_API_KEY environment variable. Set it in .env or the environment.")
        qwen_client = QwenClient(api_key=api_key, base_url=base_url, model=QWEN_MODEL)
    return qwen_client


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
def root() -> HTMLResponse:
    html_path = Path(__file__).resolve().parent.parent / "static" / "index.html"
    return HTMLResponse(html_path.read_text())


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    manager = MemoryManager(db, qwen_client)
    manager.add_conversation_message(request.user_id, "user", request.message)
    manager.decay_memories(request.user_id)
    history_records = manager.get_conversation_history(request.user_id, limit=8)
    history_text = "\n".join([f"{entry.role}: {entry.content}" for entry in history_records])
    relevant_memories = manager.retrieve_relevant_memories(request.user_id, request.message, top_k=5)

    system_prompt = (
        "You are QwenMemoryAgent, an AI assistant that remembers user preferences, goals, and facts. "
        "Use retrieved memories to personalize your answer. "
        "If you do not know a detail, answer based on the provided conversation only."
    )
    if relevant_memories:
        memory_block = "\n".join(
            [f"- {m.category}: {m.memory_text} (importance={m.importance_score:.2f})" for m in relevant_memories]
        )
        system_prompt += f"\n\nRelevant memories:\n{memory_block}"

    messages = [{"role": "system", "content": system_prompt}]
    for record in history_records:
        messages.append({"role": record.role, "content": record.content})
    messages.append({"role": "user", "content": request.message})

    try:
        client = get_qwen_client()
        response_text = client.create_chat_completion(messages, temperature=0.7)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    manager.add_conversation_message(request.user_id, "assistant", response_text)
    manager.extract_and_store_memories(request.user_id, request.message, history_text)

    return ChatResponse(
        response=response_text,
        retrieved_memories=[MemoryOut.from_orm(mem) for mem in relevant_memories],
    )


@app.get("/memory/{user_id}", response_model=List[MemoryOut])
def read_memories(user_id: str, db: Session = Depends(get_db)) -> List[MemoryOut]:
    manager = MemoryManager(db, qwen_client)
    memories = manager.get_memories(user_id)
    return [MemoryOut.from_orm(memory) for memory in memories]


@app.post("/reset_memory")
def reset_memory(request: ResetMemoryRequest, db: Session = Depends(get_db)) -> dict:
    manager = MemoryManager(db, qwen_client)
    manager.clear_memory(request.user_id)
    return {"status": "ok", "message": f"Memory cleared for user {request.user_id}"}
