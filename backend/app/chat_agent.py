import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import requests
from sqlalchemy import or_

from app.database import EmailModel, SessionLocal

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_SESSION = requests.Session()
OLLAMA_SESSION.trust_env = False

KOREAN_CHAR_PATTERN = re.compile(r"[\uac00-\ud7a3]")
TOKEN_SPLIT_PATTERN = re.compile(r"\s+")
KOREAN_PARTICLE_PATTERN = re.compile(
    r"(\uC774|\uAC00|\uC740|\uB294|\uC744|\uB97C|\uC758|\uC5D0|\uC640|\uACFC|\uB3C4|\uB85C|\uC73C\uB85C|\uB4E4)$"
)
RELATIVE_TIME_TOKEN_PATTERN = re.compile(r"^\d+(?:\uC77C|\uC8FC|days?|weeks?)$")

TIME_RANGE_PATTERNS = [
    (re.compile(r"\blast\s+(\d+)\s+days?\b", re.IGNORECASE), "days"),
    (re.compile(r"\bpast\s+(\d+)\s+days?\b", re.IGNORECASE), "days"),
    (re.compile(r"\blast\s+(\d+)\s+weeks?\b", re.IGNORECASE), "weeks"),
    (re.compile(r"\bpast\s+(\d+)\s+weeks?\b", re.IGNORECASE), "weeks"),
    (re.compile(r"\uCD5C\uADFC\s*(\d+)\s*\uC77C"), "days"),
    (re.compile(r"\uCD5C\uADFC\s*(\d+)\s*\uC8FC"), "weeks"),
]

STOPWORDS = {
    "what", "when", "where", "which", "who", "whom", "this", "that", "these",
    "those", "time", "times", "last", "week", "weeks", "recent", "latest",
    "most", "new", "was", "were", "with", "from", "have", "has", "had",
    "your", "about", "into", "after", "before", "they", "them", "then",
    "than", "please", "could", "would", "should", "there", "their", "email",
    "emails", "mail", "mails", "summary", "summarize", "recently", "today",
    "yesterday", "sent", "by", "or", "and",
    "\uCD5C\uADFC", "\uAD00\uB828", "\uC774\uBA54\uC77C", "\uBA54\uC77C", "\uB0B4\uC6A9",
    "\uB0B4\uC6A9\uB4E4", "\uC5B4\uB5A4", "\uBB34\uC2A8", "\uC788\uC5C8\uC5B4",
    "\uC788\uC5C8\uB098\uC694", "\uC788\uC5B4", "\uC54C\uB824\uC918", "\uC815\uB9AC\uD574\uC918",
    "\uC694\uC57D", "\uC694\uC57D\uD574", "\uC694\uC57D\uD574\uC918", "\uC9C0\uB09C",
    "\uC774\uBC88", "\uC8FC", "\uC8FC\uC77C", "1\uC8FC\uC77C", "\uC77C\uC8FC\uC77C",
    "\uC624\uB298", "\uC5B4\uC81C", "\uC911", "\uC5D0\uAC8C\uC11C", "\uD55C\uD14C\uC11C",
    "\uBCF4\uB0B8", "\uC628",
}


@dataclass
class QueryFilters:
    keywords: list[str]
    sender_terms: list[str]
    start_time: datetime | None
    end_time: datetime | None
    limit: int


def _parse_received_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _normalize_token(token: str) -> str:
    cleaned = token.strip(".,?!'\"():;[]{}")
    cleaned = KOREAN_PARTICLE_PATTERN.sub("", cleaned)
    return cleaned.lower()


def _extract_keywords(user_message: str) -> list[str]:
    raw_tokens = [token for token in TOKEN_SPLIT_PATTERN.split(user_message) if token.strip()]
    keywords: list[str] = []

    for token in raw_tokens:
        normalized = _normalize_token(token)
        if len(normalized) < 2:
            continue
        if normalized in STOPWORDS:
            continue
        if RELATIVE_TIME_TOKEN_PATTERN.match(normalized):
            continue
        keywords.append(normalized)

    return list(dict.fromkeys(keywords))


def _extract_sender_terms(user_message: str) -> list[str]:
    sender_terms: list[str] = []
    lowered = user_message.lower()

    english_patterns = [
        r"from\s+([a-zA-Z.\s]+?)(?:\s+(?:or|and)\s+([a-zA-Z.\s]+?))?(?:\s+emails?|\s+mail|\s+summary|$)",
        r"sent\s+by\s+([a-zA-Z.\s]+?)(?:\s+(?:or|and)\s+([a-zA-Z.\s]+?))?(?:\s+emails?|\s+mail|\s+summary|$)",
    ]
    korean_patterns = [
        r"([가-힣A-Za-z]+)(?:\s*(?:혹은|또는|or|및|와|과)\s*([가-힣A-Za-z]+))?\s*(?:에게서|한테서)\s*온",
        r"([가-힣A-Za-z]+)(?:\s*(?:혹은|또는|or|및|와|과)\s*([가-힣A-Za-z]+))?\s*(?:이|가)?\s*보낸",
    ]

    for pattern in english_patterns:
        match = re.search(pattern, lowered, re.IGNORECASE)
        if not match:
            continue
        for group in match.groups():
            if not group:
                continue
            normalized = _normalize_token(group)
            if len(normalized) >= 2:
                sender_terms.append(normalized)

    for pattern in korean_patterns:
        match = re.search(pattern, user_message)
        if not match:
            continue
        for group in match.groups():
            if not group:
                continue
            normalized = _normalize_token(group)
            if len(normalized) >= 2:
                sender_terms.append(normalized)

    return list(dict.fromkeys(sender_terms))


def _remove_sender_terms_from_keywords(keywords: list[str], sender_terms: list[str]) -> list[str]:
    if not sender_terms:
        return keywords
    sender_term_set = set(sender_terms)
    return [keyword for keyword in keywords if keyword not in sender_term_set]


def _parse_time_range(user_message: str) -> tuple[datetime | None, datetime | None]:
    lowered = user_message.lower()
    now = datetime.now(timezone.utc)

    for pattern, unit in TIME_RANGE_PATTERNS:
        match = pattern.search(user_message if KOREAN_CHAR_PATTERN.search(user_message) else lowered)
        if not match:
            continue
        amount = int(match.group(1))
        delta = timedelta(days=amount) if unit == "days" else timedelta(weeks=amount)
        return now - delta, now

    if any(
        phrase in lowered
        for phrase in ["last week", "past week", "최근 1주일", "1주일", "일주일", "지난주"]
    ):
        return now - timedelta(days=7), now

    if "today" in lowered or "\uC624\uB298" in user_message:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, now

    if "yesterday" in lowered or "\uC5B4\uC81C" in user_message:
        end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return end - timedelta(days=1), end

    return None, None


def _build_query_filters(user_message: str, default_limit: int = 5) -> QueryFilters:
    sender_terms = _extract_sender_terms(user_message)
    keywords = _remove_sender_terms_from_keywords(_extract_keywords(user_message), sender_terms)
    start_time, end_time = _parse_time_range(user_message)
    return QueryFilters(
        keywords=keywords,
        sender_terms=sender_terms,
        start_time=start_time,
        end_time=end_time,
        limit=default_limit,
    )


def _sender_matches(sender_value: str, sender_terms: list[str]) -> bool:
    if not sender_terms:
        return True
    sender_lower = (sender_value or "").lower()
    return any(term in sender_lower for term in sender_terms)


def _semantic_search_emails(user_message: str, n_results: int = 10) -> list[dict]:
    try:
        from app.vector_store import search_emails

        return search_emails(user_message, n_results=n_results)
    except Exception:
        return []


def _keyword_search_emails(filters: QueryFilters, limit: int = 10) -> list[dict]:
    if not filters.keywords and not filters.sender_terms:
        return []

    db = SessionLocal()
    try:
        conditions = []
        for keyword in filters.keywords[:10]:
            like_pattern = f"%{keyword}%"
            conditions.extend(
                [
                    EmailModel.subject.ilike(like_pattern),
                    EmailModel.body.ilike(like_pattern),
                    EmailModel.sender.ilike(like_pattern),
                ]
            )
        for sender_term in filters.sender_terms[:10]:
            conditions.append(EmailModel.sender.ilike(f"%{sender_term}%"))

        candidate_rows = (
            db.query(EmailModel)
            .filter(or_(*conditions))
            .order_by(EmailModel.received_time.desc())
            .limit(200)
            .all()
        )

        scored_rows = []
        for row in candidate_rows:
            received_at = _parse_received_time(row.received_time)
            if filters.start_time and (not received_at or received_at < filters.start_time):
                continue
            if filters.end_time and received_at and received_at > filters.end_time:
                continue

            sender = (row.sender or "").lower()
            if not _sender_matches(sender, filters.sender_terms):
                continue

            subject = (row.subject or "").lower()
            body = (row.body or "").lower()
            subject_hits = 0
            body_hits = 0
            sender_hits = 0
            score = 0

            for keyword in filters.keywords:
                if keyword in subject:
                    subject_hits += 1
                    score += 12
                if keyword in body:
                    body_hits += 1
                    score += 3
                if keyword in sender:
                    sender_hits += 1
                    score += 1

            keyword_hits = subject_hits + body_hits + sender_hits
            if filters.keywords and keyword_hits == 0:
                continue

            if filters.sender_terms:
                score += 20
                sender_hits += 3

            scored_rows.append((subject_hits, score, keyword_hits, row.received_time or "", row))

        scored_rows.sort(key=lambda item: (item[0], item[1], item[2], item[3]), reverse=True)
        top_rows = [row for _, _, _, _, row in scored_rows[:limit]]

        return [
            {
                "id": row.id,
                "metadata": {
                    "subject": row.subject,
                    "sender": row.sender,
                    "sender_email": row.sender_email,
                    "received_time": row.received_time,
                    "summary": row.summary or "",
                    "priority": row.priority or "",
                },
                "preview": row.body[:1200] if row.body else "",
            }
            for row in top_rows
        ]
    finally:
        db.close()


def _score_keyword_matches(filters: QueryFilters, subject: str, preview: str, sender: str) -> tuple[int, int]:
    subject_hits = 0
    weighted_hits = 0

    for keyword in filters.keywords:
        if keyword in subject:
            subject_hits += 1
            weighted_hits += 3
        if keyword in preview:
            weighted_hits += 1
        if keyword in sender:
            weighted_hits += 1

    if filters.sender_terms:
        sender_match_count = sum(1 for term in filters.sender_terms if term in sender)
        if sender_match_count == 0:
            return subject_hits, -1
        weighted_hits += sender_match_count * 4

    return subject_hits, weighted_hits


def _rank_relevant_emails(filters: QueryFilters, semantic_results: list[dict], keyword_results: list[dict]) -> list[dict]:
    merged_by_id: dict[str, dict] = {}

    for source_name, results in (("semantic", semantic_results), ("keyword", keyword_results)):
        for index, email in enumerate(results):
            email_id = email.get("id")
            if not email_id:
                continue

            existing = merged_by_id.get(email_id)
            if not existing:
                merged_by_id[email_id] = {
                    **email,
                    "_sources": {source_name},
                    "_best_index": index,
                }
            else:
                existing["_sources"].add(source_name)
                existing["_best_index"] = min(existing["_best_index"], index)

    scored_results = []
    now = datetime.now(timezone.utc)

    for email in merged_by_id.values():
        metadata = email["metadata"]
        subject = (metadata.get("subject") or "").lower()
        sender = (metadata.get("sender") or "").lower()
        preview = (email.get("preview") or "").lower()
        received_time = metadata.get("received_time") or ""
        received_at = _parse_received_time(received_time)

        if filters.start_time and (not received_at or received_at < filters.start_time):
            continue
        if filters.end_time and received_at and received_at > filters.end_time:
            continue

        subject_hits, weighted_hits = _score_keyword_matches(filters, subject, preview, sender)
        if filters.sender_terms and weighted_hits < 0:
            continue
        if filters.keywords and weighted_hits == 0:
            continue

        score = 0
        if "keyword" in email["_sources"]:
            score += 14
        if "semantic" in email["_sources"]:
            score += 6

        score += subject_hits * 8
        score += weighted_hits * 4

        if received_at:
            age_days = max((now - received_at).total_seconds() / 86400, 0)
            score += max(0, 7 - age_days)

        scored_results.append((subject_hits, score, weighted_hits, received_time, -email["_best_index"], email))

    scored_results.sort(reverse=True)

    if filters.keywords:
        subject_priority = [item for item in scored_results if item[0] > 0]
        if len(subject_priority) >= min(3, filters.limit):
            scored_results = subject_priority

    return [email for _, _, _, _, _, email in scored_results[: filters.limit]]


def _build_email_context(relevant_emails: list[dict]) -> str:
    if not relevant_emails:
        return "\n\n[No relevant emails found]"

    lines = ["", "", "[Relevant emails found]"]
    for index, email in enumerate(relevant_emails, 1):
        meta = email["metadata"]
        preview = (email.get("preview") or "").replace("\r", " ").replace("\n", " ").strip()
        preview = preview[:700]
        lines.extend(
            [
                f"--- Email {index} ---",
                f"Subject  : {meta.get('subject') or 'No Subject'}",
                f"From     : {meta.get('sender') or 'Unknown Sender'} <{meta.get('sender_email') or 'Unknown Email'}>",
                f"Received : {meta.get('received_time') or 'Unknown Time'}",
                f"Preview  : {preview or 'No preview available.'}",
            ]
        )
    return "\n".join(lines)


def _build_fallback_answer(relevant_emails: list[dict]) -> str:
    if not relevant_emails:
        return "I could not find a matching email in the currently synced data."

    lines = ["I could not reach the LLM, but I found matching synced emails."]
    for email in relevant_emails[:5]:
        meta = email["metadata"]
        preview = (email.get("preview") or "").replace("\r", " ").replace("\n", " ").strip()
        preview = preview[:140] + ("..." if len(preview) > 140 else "")
        lines.append(
            f"- {meta.get('received_time', 'Unknown Time')} | "
            f"{meta.get('subject', 'No Subject')} | "
            f"{meta.get('sender', 'Unknown Sender')} | "
            f"{preview or 'No preview available.'}"
        )
    return "\n".join(lines)


def chat_with_agent(user_message: str, conversation_history: list) -> str:
    filters = _build_query_filters(user_message, default_limit=5)
    semantic_results = _semantic_search_emails(user_message, n_results=10)
    keyword_results = _keyword_search_emails(filters, limit=10)
    relevant_emails = _rank_relevant_emails(filters, semantic_results, keyword_results)

    email_context = _build_email_context(relevant_emails)

    history_text = ""
    for message in conversation_history:
        role = "User" if message["role"] == "user" else "Assistant"
        history_text += f"{role}: {message['content']}\n"

    prompt = f"""You are an AI assistant that helps users search and understand their Outlook emails.
Answer based only on the email data provided below.
If no relevant emails are found, say so honestly.
Always mention the subject, sender, and date when referencing an email.
Treat the explicit "From" field in each email block as the true sender. Do not replace it with names mentioned inside forwarded content.
If the user asks for a summary of recent emails, group the answer into short themes instead of listing raw data only.
Respond in English by default unless the user explicitly asks for another language.
{email_context}

Conversation so far:
{history_text}
User: {user_message}
Assistant:"""

    try:
        response = OLLAMA_SESSION.post(
            OLLAMA_URL,
            json={"model": "llama3", "prompt": prompt, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception:
        return _build_fallback_answer(relevant_emails)
