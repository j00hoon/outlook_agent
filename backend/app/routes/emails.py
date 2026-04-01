# app/routes/emails.py
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import EmailModel, get_db
from app.outlook_reader import get_recent_emails, get_inbox_subfolders

router = APIRouter(prefix="/emails")

# Folder list endpoint
@router.get("/folders")
async def list_folders():
    try:
        folders = get_inbox_subfolders()
        return {"folders": folders}
    except Exception as e:
        # Always return JSON, even on error
        return JSONResponse(status_code=500, content={"error": str(e), "folders": []})

# Emails endpoint
@router.get("/")
async def get_emails(folder: str = Query(None), limit: int = 10):
    try:
        emails = get_recent_emails(limit=limit, folder_name=folder)
        return {"emails": emails}
    except Exception as e:
        # Always return JSON, even on error
        return JSONResponse(status_code=500, content={"error": str(e), "emails": []})


@router.get("/db/count")
async def get_db_email_count(db: Session = Depends(get_db)):
    try:
        return {"count": db.query(EmailModel).count()}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e), "count": 0})


@router.get("/db")
async def get_db_emails(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    try:
        total = db.query(EmailModel).count()
        emails = (
            db.query(EmailModel)
            .order_by(EmailModel.received_time.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "emails": [
                {
                    "id": email.id,
                    "subject": email.subject,
                    "sender": email.sender,
                    "sender_email": email.sender_email,
                    "body": email.body,
                    "summary": email.summary,
                    "action_items": email.action_items,
                    "priority": email.priority,
                    "received_time": email.received_time,
                }
                for email in emails
            ],
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "total": 0, "limit": limit, "offset": offset, "emails": []},
        )
