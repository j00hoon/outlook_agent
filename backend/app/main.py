# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.emails import router as email_router
from app.routes.chat import router as chat_router
from app.outlook_reader import fetch_and_store_emails
from app.vector_store import index_emails_to_vector

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(email_router)
app.include_router(chat_router)


@app.on_event("startup")
async def startup_event():
    """
    On server start:
    1. Sync emails from Outlook to SQLite DB
    2. Index new emails into ChromaDB for vector search
    """
    print("Syncing emails from Outlook...")
    count = fetch_and_store_emails(limit=3000, days=90)
    print(f"Saved {count} new emails to DB")

    print("Indexing emails into vector store...")
    indexed = index_emails_to_vector()
    print(f"Indexed {indexed} emails - Ready!")


@app.post("/sync")
async def sync_emails():
    """
    Manually trigger email sync + re-index.
    Call this after receiving new emails.
    """
    count   = fetch_and_store_emails(limit=3000, days=90)
    indexed = index_emails_to_vector()
    return {"synced": count, "indexed": indexed}