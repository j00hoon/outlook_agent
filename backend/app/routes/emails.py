# app/routes/emails.py
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
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