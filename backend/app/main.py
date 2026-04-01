import hashlib
from datetime import datetime, timezone
from typing import Optional

import redis
from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.outlook_reader import fetch_and_store_emails, get_inbox_subfolders
from app.routes.chat import router as chat_router
from app.routes.emails import router as email_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(email_router)
app.include_router(chat_router)

cache = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


class ChatRequest(BaseModel):
    prompt: str
    history: list[dict[str, str]] = []


class SyncRequest(BaseModel):
    folder_names: Optional[list[str]] = None


@app.post("/api/sync_emails")
async def sync_emails(request: Optional[SyncRequest] = Body(default=None)):
    try:
        requested_folder_names = request.folder_names if request and request.folder_names else []
        cleaned_folder_names = [name.strip() for name in requested_folder_names if name and name.strip()]

        if not cleaned_folder_names:
            raise HTTPException(status_code=400, detail="Select at least one Inbox folder.")

        available_folders = get_inbox_subfolders()
        canonical_folder_names: list[str] = []
        seen_folder_names = set()

        for folder_name in cleaned_folder_names:
            matched_folder_name = "Inbox" if folder_name.lower() == "inbox" else next(
                (name for name in available_folders if name.lower() == folder_name.lower()),
                None,
            )
            if not matched_folder_name:
                raise HTTPException(
                    status_code=400,
                    detail=f"Folder '{folder_name}' was not found under Inbox.",
                )
            folder_key = matched_folder_name.lower()
            if folder_key in seen_folder_names:
                continue
            seen_folder_names.add(folder_key)
            canonical_folder_names.append(matched_folder_name)

        total_saved_count = 0
        synced_folders: list[str] = []
        current_sync_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        for folder_name in canonical_folder_names:
            cache_folder_key = "__inbox__" if folder_name == "Inbox" else folder_name
            last_sync_key = f"outlook:last_sync_time:{cache_folder_key}"
            last_sync_time = cache.get(last_sync_key)
            parsed_last_sync = None
            if last_sync_time:
                parsed_last_sync = datetime.fromisoformat(last_sync_time.replace("Z", "+00:00"))

            saved_count = fetch_and_store_emails(
                folder_name=None if folder_name == "Inbox" else folder_name,
                last_sync_time=parsed_last_sync,
            )
            total_saved_count += saved_count
            synced_folders.append(folder_name)
            cache.set(last_sync_key, current_sync_time)

        indexed_count = 0
        indexing_warning = None
        try:
            from app.vector_store import index_emails_to_vector

            indexed_count = index_emails_to_vector()
        except Exception as exc:
            indexing_warning = f"Vector indexing skipped: {str(exc)}"

        return {
            "status": "success",
            "message": f"Synced {', '.join(synced_folders)} successfully.",
            "count": total_saved_count,
            "indexed_count": indexed_count,
            "warning": indexing_warning,
            "folder_names": synced_folders,
            "last_sync": current_sync_time,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Sync Error: {str(exc)}")


@app.post("/api/chat")
async def chat_with_agent(request: ChatRequest):
    prompt = request.prompt.strip()
    history = request.history or []

    cache_payload = f"v7|{prompt}|{history}"
    prompt_hash = hashlib.md5(cache_payload.encode()).hexdigest()
    cache_key = f"chat:cache:{prompt_hash}"

    cached_answer = cache.get(cache_key)
    if cached_answer:
        return {
            "answer": cached_answer,
            "is_cached": True,
            "message": "Response served from Redis cache.",
        }

    from app.chat_agent import chat_with_agent as run_chat_agent

    real_response = run_chat_agent(prompt, history)
    cache.setex(cache_key, 3600, real_response)

    return {
        "answer": real_response,
        "is_cached": False,
        "message": "Response generated from retrieved email context.",
    }
