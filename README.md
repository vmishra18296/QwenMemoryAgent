# QwenMemoryAgent

A memory-enhanced AI assistant prototype built with FastAPI, SQLite, and Qwen Cloud.

## What it includes

- REST chat API with multi-turn session support
- Persistent memory storage for user-specific preferences, goals, facts, and other long-term data
- Memory extraction using Qwen model prompts
- Memory retrieval and ranking using relevance, importance, and recency
- Memory decay logic for gradual forgetting of unused memories
- Simple frontend chat UI for demonstration

## Project structure

- `app/main.py` - FastAPI application and endpoints
- `app/db.py` - database engine and session management
- `app/models.py` - SQLAlchemy models for memory and conversation history
- `app/schemas.py` - Pydantic request/response models
- `app/qwen_client.py` - Qwen Cloud API wrapper
- `app/alibaba_client.py` - Alibaba Cloud SDK helper for ECS provisioning
- `deploy_alibaba.py` - Alibaba Cloud deployment helper script
- `alibaba_deploy.sh` - convenience wrapper for Alibaba Cloud deployment
- `static/index.html` - simple browser chat UI
- `requirements.txt` - Python dependencies
- `.env.example` - environment variable template

## Alibaba Cloud Deployment

This project includes an Alibaba Cloud deployment helper that demonstrates Alibaba Cloud API usage via `aliyun-python-sdk-core` and `aliyun-python-sdk-ecs`.

1. Set Alibaba Cloud credentials in `.env`:

```bash
ALIBABA_CLOUD_ACCESS_KEY_ID=your_alibaba_access_key_id
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_alibaba_access_key_secret
ALIBABA_CLOUD_REGION=cn-hangzhou
```

2. Activate the virtual environment:

```bash
source .venv/bin/activate
```

3. List ECS instances:

```bash
python deploy_alibaba.py --list
```

4. Create a new ECS instance:

```bash
python deploy_alibaba.py --create --security-group-id sg-xxxxxxxx
```

5. Delete an ECS instance:

```bash
python deploy_alibaba.py --delete i-xxxxxxxx
```

## Setup

1. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy environment variables:

```bash
cp .env.example .env
```

4. Fill in `QWEN_API_KEY` in `.env`.

5. Run the app:

```bash
uvicorn app.main:app --reload
```

6. Open the demo UI:

- http://127.0.0.1:8000/

## API Endpoints

- `POST /chat`
  - Input: `user_id`, `message`
  - Output: assistant response and retrieved memories

- `GET /memory/{user_id}`
  - Returns stored memory entries for the user

- `POST /reset_memory`
  - Input: `user_id`
  - Clears stored memories and conversation history for that user

## Example request

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user-123", "message":"I like Python and want to prepare for interviews."}'
```

## Notes

- The memory layer avoids storing trivial chat noise.
- Retrieved memories are ranked before being passed to Qwen.
- Memory importance decays over time and may be deleted when unused.
- Duplicate memories are merged and updated instead of creating redundant entries.
