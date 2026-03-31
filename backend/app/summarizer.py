# app/summarizer.py
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"

def summarize_email(subject, body):
    prompt = f"""
You are an email assistant.

Read the email and return ONLY valid JSON.

Required JSON format:
{{
  "summary": "short summary",
  "action_items": ["item1", "item2"],
  "priority": "High"
}}

Rules:
- summary must be short
- action_items must always be an array
- priority must be only High, Medium, or Low
- do not include markdown
- do not include explanation text
- do not include code block markers

Email Subject:
{subject}

Email Body:
{body[:4000]}
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()
        result = response.json()

        raw_text = result.get("response", "").strip()

        # Remove markdown code block if model returns ```json ... ```
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        try:
            # Find first JSON object block
            start_idx = raw_text.find("{")
            end_idx = raw_text.rfind("}")

            if start_idx != -1 and end_idx != -1:
                raw_text = raw_text[start_idx:end_idx + 1]

            parsed = json.loads(raw_text)

            return {
                "summary": parsed.get("summary", "N/A"),
                "action_items": parsed.get("action_items", []),
                "priority": parsed.get("priority", "N/A"),
            }

        except Exception:
            return {
                "summary": raw_text if raw_text else "Failed to summarize",
                "action_items": [],
                "priority": "N/A",
            }

    except Exception as e:
        return {
            "summary": f"Failed to summarize: {str(e)}",
            "action_items": [],
            "priority": "N/A",
        }