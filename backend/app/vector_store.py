import os
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
from app.database import SessionLocal, EmailModel

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# Persistent ChromaDB stored in backend/chroma_db folder
chroma_client = chromadb.PersistentClient(path="./chroma_db")

DEFAULT_MODEL_DIR = (
    Path(__file__).resolve().parents[1]
    / "models"
    / "paraphrase-multilingual-MiniLM-L12-v2"
)


def _resolve_embedding_model_path() -> str:
    configured_path = os.getenv("EMBEDDING_MODEL_PATH")
    model_path = Path(configured_path).expanduser() if configured_path else DEFAULT_MODEL_DIR

    if not model_path.exists():
        raise FileNotFoundError(
            f"Embedding model not found: {model_path}. "
            "Download the model into backend/models or set EMBEDDING_MODEL_PATH."
        )

    return str(model_path)


embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=_resolve_embedding_model_path()  # supports Korean + English
)

collection = chroma_client.get_or_create_collection(
    name="emails",
    embedding_function=embedding_fn
)


def index_emails_to_vector():
    """
    Index emails from DB into ChromaDB for semantic search.
    Skips emails already indexed.
    """
    db = SessionLocal()
    emails = db.query(EmailModel).all()
    db.close()

    existing_ids = set(collection.get()["ids"])
    new_emails   = [e for e in emails if e.id not in existing_ids]

    if not new_emails:
        print("No new emails to index")
        return 0

    # Add in batches to avoid memory issues
    batch_size = 50
    for i in range(0, len(new_emails), batch_size):
        batch = new_emails[i : i + batch_size]
        collection.add(
            ids       = [e.id for e in batch],
            documents = [
                f"Subject: {e.subject}\nFrom: {e.sender}\nBody: {e.body[:500]}"
                for e in batch
            ],
            metadatas = [
                {
                    "subject":       e.subject,
                    "sender":        e.sender,
                    "sender_email":  e.sender_email,
                    "received_time": e.received_time,
                    "summary":       e.summary or "",
                    "priority":      e.priority or "",
                }
                for e in batch
            ]
        )

    print(f"Indexed {len(new_emails)} emails")
    return len(new_emails)


def search_emails(query: str, n_results: int = 5):
    """
    Search emails using natural language query.
    Returns list of matched emails with metadata.
    """
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )

    emails = []
    if results["ids"][0]:
        for i, email_id in enumerate(results["ids"][0]):
            emails.append({
                "id":       email_id,
                "metadata": results["metadatas"][0][i],
                "preview":  results["documents"][0][i],
            })
    return emails
