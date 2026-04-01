// services/chatService.ts
const API_URL = "http://localhost:8000";

export interface Message {
  role: "user" | "assistant";
  content: string;
}

export async function sendChatMessage(
  message: string,
  history: Message[]
): Promise<string> {
  const response = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });

  if (!response.ok) throw new Error("Chat API error");

  const data = await response.json();
  return data.reply;
}
