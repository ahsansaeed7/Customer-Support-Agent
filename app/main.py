"""
FastAPI entrypoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.agent.loop import run_agent_turn
from app.agent.state import load_history, save_history
from app.webhook.router import router as whatsapp_router
from app.dashboard_api.router import router as dashboard_router

app = FastAPI(title="WhatsApp Travel Agent")

# Allows the Next.js dashboard (running on localhost:3000) to call this API
# (running on localhost:8000) — different ports count as different origins
# to the browser, so this is required for local dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(whatsapp_router)
app.include_router(dashboard_router)


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
    """Kept for direct testing via /docs — the real path is /webhook/whatsapp."""
    history = load_history(req.phone_number)
    reply, updated_history = run_agent_turn(req.phone_number, req.message, history)
    save_history(req.phone_number, updated_history)
    return ChatResponse(reply=reply)
