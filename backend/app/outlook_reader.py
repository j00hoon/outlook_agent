# app/outlook_reader.py
import win32com.client
import pythoncom
import hashlib
import json
from datetime import datetime, timedelta
from app.database import SessionLocal, EmailModel


def get_inbox_subfolders():
    """Return the names of subfolders under Inbox"""
    pythoncom.CoInitialize()
    try:
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        inbox = outlook.GetDefaultFolder(6)
        subfolders = [folder.Name for folder in inbox.Folders]
        return subfolders
    finally:
        pythoncom.CoUninitialize()


def _get_target_folder(namespace, folder_name=None):
    inbox = namespace.GetDefaultFolder(6)

    if not folder_name:
        return inbox

    for folder in inbox.Folders:
        if folder.Name.lower() == folder_name.lower():
            return folder

    raise ValueError(f"Folder '{folder_name}' was not found under Inbox.")


def fetch_and_store_emails(
    limit: int = 3000,
    days: int = 90,
    folder_name=None,
    last_sync_time=None,
):
    """
    Fetch emails from an Inbox folder in Outlook and store in SQLite DB.
    Skips emails already stored (no duplicates).
    """
    pythoncom.CoInitialize()
    try:
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        target_folder = _get_target_folder(outlook, folder_name)
        messages = target_folder.Items
        messages.Sort("[ReceivedTime]", True)  # Sort newest first

        cutoff_date = datetime.now() - timedelta(days=days)
        sync_cutoff = None
        if last_sync_time is not None:
            sync_cutoff = last_sync_time.astimezone().replace(tzinfo=None)

        db = SessionLocal()
        saved_count = 0

        for i, message in enumerate(messages):
            if i >= limit:
                break
            try:
                # Stop when emails are older than cutoff date
                received_raw = getattr(message, "ReceivedTime", None)
                if received_raw is None:
                    continue

                received_dt = datetime(
                    received_raw.year, received_raw.month, received_raw.day,
                    received_raw.hour, received_raw.minute, received_raw.second
                )
                if sync_cutoff and received_dt <= sync_cutoff:
                    break
                if received_dt < cutoff_date:
                    break

                subject      = getattr(message, "Subject", "") or "No Subject"
                sender       = getattr(message, "SenderName", "") or "Unknown"
                sender_email = getattr(message, "SenderEmailAddress", "") or ""
                body         = getattr(message, "Body", "") or ""

                # Generate unique ID from subject + sender + time
                unique_str = f"{subject}{sender}{received_raw}"
                email_id   = hashlib.md5(unique_str.encode()).hexdigest()

                # Skip if already in DB
                if db.query(EmailModel).filter(EmailModel.id == email_id).first():
                    continue

                email = EmailModel(
                    id           = email_id,
                    subject      = subject,
                    sender       = sender,
                    sender_email = sender_email,
                    body         = body[:3000],
                    summary      = "",           # skip summarization for now
                    action_items = json.dumps([]),
                    priority     = "",
                    received_time= str(received_raw)
                )
                db.add(email)
                saved_count += 1

            except Exception as e:
                print(f"Error processing email: {e}")
                continue

        db.commit()
        db.close()
        return saved_count

    finally:
        pythoncom.CoUninitialize()


def get_emails_from_db(limit: int = 20, skip: int = 0):
    """
    Return emails from SQLite DB (fast, no Outlook needed).
    """
    db = SessionLocal()
    rows = (
        db.query(EmailModel)
          .order_by(EmailModel.received_time.desc())
          .offset(skip)
          .limit(limit)
          .all()
    )
    db.close()

    return [
        {
            "subject":      r.subject,
            "sender":       r.sender,
            "received_time":r.received_time,
            "summary":      r.summary,
            "action_items": json.loads(r.action_items) if r.action_items else [],
            "priority":     r.priority,
        }
        for r in rows
    ]


def get_recent_emails(limit=10, folder_name=None):
    """
    Original function kept for compatibility.
    Now reads from DB instead of Outlook directly.
    """
    return get_emails_from_db(limit=limit)
