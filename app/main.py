"""
FastAPI entrypoint.
"""

from fastapi import FastAPI
from pydantic import BaseModel

from app.agent.loop import run_agent_turn
from app.agent.state import load_history, save_history

app = FastAPI(title="WhatsApp Travel Agent")


class ChatRequest(BaseModel):
    phone_number: str
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    history = load_history(req.phone_number)
    reply, updated_history = run_agent_turn(req.phone_number, req.message, history)
    save_history(req.phone_number, updated_history)
    return ChatResponse(reply=reply)
