# app/chat_agent.py
import requests
from app.vector_store import search_emails

OLLAMA_URL = "http://localhost:11434/api/generate"


def summarize_on_demand(subject: str, body: str) -> str:
    """
    Summarize a single email on demand using Ollama.
    Called only when an email is retrieved in search.
    """
    prompt = f"""Summarize this email in 2-3 sentences.
Be concise and highlight the key point and any action required.

Subject: {subject}
Body: {body[:2000]}

Summary:"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": "llama3", "prompt": prompt, "stream": False},
            timeout=60
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        return f"Summary unavailable: {str(e)}"


def chat_with_agent(user_message: str, conversation_history: list) -> str:
    """
    Search relevant emails using vector search,
    summarize them on demand, then generate a response using Ollama.
    """

    # Step 1: Find relevant emails via semantic search
    relevant_emails = search_emails(user_message, n_results=5)

    # Step 2: Summarize each result on demand + build context
    if relevant_emails:
        email_context = "\n\n[Relevant emails found]\n"
        for i, email in enumerate(relevant_emails, 1):
            meta = email["metadata"]

            # Summarize only this email right now
            summary = summarize_on_demand(
                subject=meta["subject"],
                body=email["preview"]
            )

            email_context += f"""
--- Email {i} ---
Subject  : {meta['subject']}
From     : {meta['sender']} <{meta['sender_email']}>
Received : {meta['received_time']}
Summary  : {summary}
"""
    else:
        email_context = "\n\n[No relevant emails found]"

    # Step 3: Build conversation history as plain text
    history_text = ""
    for msg in conversation_history:
        role = "User" if msg["role"] == "user" else "Assistant"
        history_text += f"{role}: {msg['content']}\n"

    # Step 4: Build prompt
    prompt = f"""You are an AI assistant that helps users search and understand their Outlook emails.
Answer based only on the email data provided below.
If no relevant emails are found, say so honestly.
Always mention the subject, sender, and date when referencing an email.
Respond in the same language the user uses.
{email_context}

Conversation so far:
{history_text}
User: {user_message}
Assistant:"""

    # Step 5: Call Ollama API
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": "llama3", "prompt": prompt, "stream": False},
            timeout=120
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()

    except Exception as e:
        return f"Error: {str(e)}"