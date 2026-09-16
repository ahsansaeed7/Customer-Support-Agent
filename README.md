# WhatsApp Travel Agent

Scaffold for an agent-with-tools WhatsApp travel booking system.

## Build order
1. DB schema + seed data
2. Core tools as plain, independently-testable Python functions
3. Agent loop tested via CLI (no WhatsApp yet)
4. FastAPI /chat endpoint wrapping the agent loop
5. WhatsApp integration (start with Twilio sandbox)
6. Redis queue + idempotency + async workers
7. Payment flow + HITL dashboard
8. Edge cases: 24h window, booking holds, rate limiting

