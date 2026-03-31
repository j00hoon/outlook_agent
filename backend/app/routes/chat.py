# app/routes/chat.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.chat_agent import chat_with_agent

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    history: list = []  # [{"role": "user"/"assistant", "content": "..."}]


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Receive user message, search emails, return AI response.
    """
    reply = chat_with_agent(request.message, request.history)
    return ChatResponse(reply=reply)