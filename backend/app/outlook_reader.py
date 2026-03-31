# app/outlook_reader.py
import win32com.client
import pythoncom
from app.summarizer import summarize_email

def get_inbox_subfolders():
    """Return the names of subfolders under Inbox"""
    pythoncom.CoInitialize()
    try:
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        inbox = outlook.GetDefaultFolder(6)  # 6 = Inbox
        subfolders = [folder.Name for folder in inbox.Folders]
        return subfolders
    finally:
        pythoncom.CoUninitialize()

def get_recent_emails(limit=10, folder_name=None):
    """Return recent emails with summary, action items, and priority"""
    pythoncom.CoInitialize()
    try:
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")

        # Select folder
        inbox = outlook.GetDefaultFolder(6)  # Default Inbox
        folder = inbox

        if folder_name:
            try:
                # Try to find selected subfolder under Inbox
                folder = inbox.Folders[folder_name]
            except Exception:
                # Fallback to Inbox if folder not found
                folder = inbox

        messages = folder.Items
        messages.Sort("[ReceivedTime]", True)  # Sort newest first

        emails = []

        for i, message in enumerate(messages):
            if i >= limit:
                break

            # Safely read Outlook fields
            subject = getattr(message, "Subject", "") or "No Subject"
            body = getattr(message, "Body", "") or ""

            sender = getattr(message, "SenderName", "") or "Unknown Sender"

            received_time_raw = getattr(message, "ReceivedTime", None)
            received_time = (
                str(received_time_raw) if received_time_raw else "Unknown Time"
            )

            # Summarize email using Ollama
            summary_data = summarize_email(subject, body)

            emails.append({
                "subject": subject,
                "sender": sender,
                "received_time": received_time,
                "summary": summary_data.get("summary", "N/A"),
                "action_items": summary_data.get("action_items", []),
                "priority": summary_data.get("priority", "N/A"),
            })

        return emails

    finally:
        pythoncom.CoUninitialize()