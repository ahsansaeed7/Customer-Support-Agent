# WhatsApp Travel Agency Agent

An AI agent that handles end-to-end travel bookings over WhatsApp — searching tours, creating draft bookings, sharing payment details, and handing off to a human for payment verification — backed by a human-in-the-loop dashboard for approvals.

Built as a **tool-calling agent** (not a fixed workflow): an LLM decides which tools to call based on the customer's message and conversation context, rather than following a hardcoded sequence of steps.

---

## Architecture

```mermaid
flowchart TD
    A[Customer on WhatsApp] -->|message| B[Meta WhatsApp Cloud API]
    B -->|webhook POST| C[FastAPI: /webhook/whatsapp]
    C --> D[Load session history<br/>Postgres: conversation_sessions]
    D --> E[Agent Loop<br/>Groq LLM + tool schemas]

    E -->|tool call| F{Which tool?}
    F -->|search_tours| G[(Postgres: tours)]
    F -->|create_booking_draft| H[(Postgres: bookings, users)]
    F -->|confirm_booking_intent| H
    F -->|cancel_booking| H
    F -->|get_payment_details| I[Real bank info<br/>from .env config]
    F -->|escalate_to_human| J[Canned message<br/>+ human_takeover flag]

    F -->|result| E
    E -->|final reply| K[Save session history]
    K --> L[Meta WhatsApp Cloud API]
    L -->|reply| A

    M[Human Agent] -->|views| N[Next.js Dashboard]
    N -->|GET /dashboard/bookings| O[FastAPI Dashboard API]
    O --> H
    N -->|POST .../approve| O
    O -->|status -> confirmed| H
    O -->|send confirmation| L
```

---

## Key design decisions

**Agent, not workflow.** Customer conversations don't follow a fixed path — they backtrack, ask unrelated questions, and change their minds. Tools (`search_tours`, `create_booking_draft`, etc.) are plain Python functions with JSON schemas; the LLM decides which to call and when, rather than a hardcoded step sequence.

**No custom orchestration framework.** No LangGraph/CrewAI/Agents SDK — the agent loop is a straightforward `while` loop (see `app/agent/loop.py`) calling Groq's tool-calling API directly. For a single agent with a handful of tools, a framework adds dependency risk and abstraction overhead without solving a real problem here.

**Never let the LLM invent facts.** Prices, dates, booking status, and payment details are always computed server-side or pulled from real config/DB — never left for the model to "fill in." The system prompt explicitly forbids claiming an action happened without a tool call backing it up. (This was tightened iteratively after catching the model hallucinate a "confirmed" status and fictional bank account details during testing.)

**Sessions decoupled from the `users` table.** `conversation_sessions` is keyed directly by phone number and has no required foreign key to `users`. This means casual browsers ("how much is Bali?") get conversation memory without ever creating a permanent customer record — `users` rows are only created lazily, at the moment someone actually creates a booking draft. This keeps the busiest code path (every inbound message) to a single DB write instead of two, and keeps the `users` table meaningful (real leads only).

**Phone number is never customer- or LLM-supplied.** Early testing revealed the agent asking customers for their WhatsApp number and using whatever they typed — which could mismatch the real sender ID from the webhook. The agent loop now forcibly overrides any `phone_number` argument the LLM tries to pass with the actual verified sender number from the webhook payload.

**Escalation is a hard short-circuit.** When the agent calls `escalate_to_human` (for prompt injection attempts, off-topic abuse, or requests it can't fulfill), the loop returns a fixed, hardcoded message — not anything the LLM generates for that turn. This was deliberately built to survive injection attempts that might otherwise partially succeed in swaying the model's own phrasing.

---

## Tech stack

| Layer | Technology |
|---|---|
| LLM | Groq (`openai/gpt-oss-120b`) — tool-calling, no orchestration framework |
| Backend | FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL + `pgvector` (for future semantic search over policy docs) |
| Messaging | Meta WhatsApp Cloud API |
| Dashboard | Next.js (App Router) + Tailwind CSS |
| Local dev | Docker Compose (Postgres + Redis), ngrok (webhook tunneling) |

---

## Folder structure

```
whatsapp-travel-agent/
├── app/
│   ├── main.py                    # FastAPI entrypoint
│   ├── config.py                  # env var loading
│   ├── webhook/
│   │   └── router.py              # Meta webhook: verification handshake + inbound messages
│   ├── agent/
│   │   ├── loop.py                # core tool-calling loop
│   │   ├── prompts.py             # system prompt (scope, guardrails, formatting rules)
│   │   ├── state.py               # session persistence (Postgres-backed)
│   │   └── tools/
│   │       ├── search_tours.py
│   │       ├── booking.py             # create_booking_draft
│   │       ├── booking_status.py      # confirm_booking_intent, cancel_booking
│   │       ├── payment_info.py        # get_payment_details (real config, never invented)
│   │       └── escalate.py            # escalate_to_human
│   ├── whatsapp/
│   │   └── client.py               # Meta Graph API client (send_text)
│   ├── dashboard_api/
│   │   └── router.py               # bookings list + approve endpoints
│   └── db/
│       ├── models.py                # SQLAlchemy models
│       ├── session.py
│       ├── crud.py
│       └── seed.py                  # seeds fake tour data for local dev
├── frontend/                        # Next.js human-agent dashboard
├── alembic/                         # DB migrations
├── docker-compose.yml                # Postgres (pgvector) + Redis
└── requirements.txt
```

---

## Getting started

### Prerequisites
- Python 3.12+
- Node.js
- Docker Desktop
- A [Groq API key](https://console.groq.com)
- A Meta Developer app with the WhatsApp product added ([developers.facebook.com](https://developers.facebook.com))

### 1. Clone and install
```bash
git clone <this-repo>
cd whatsapp-travel-agent
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Start Postgres + Redis
```bash
docker compose up -d
```
Enable required extensions (first time only):
```bash
docker exec -it travel_agent_db psql -U travel_agent -d travel_agent_db
```
```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 3. Environment variables
Copy `.env.example` to `.env` and fill in:

```
DATABASE_URL=postgresql://travel_agent:devpassword@localhost:5432/travel_agent_db
REDIS_URL=redis://localhost:6379/0

GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-120b

META_ACCESS_TOKEN=
META_PHONE_NUMBER_ID=
META_VERIFY_TOKEN=
META_APP_SECRET=

BANK_ACCOUNT_NAME=
BANK_ACCOUNT_NUMBER=
BANK_SWIFT_BIC=
BANK_NAME=
```

### 4. Run migrations and seed data
```bash
alembic upgrade head
python -m app.db.seed
```

### 5. Run the backend
```bash
uvicorn app.main:app --reload
```

### 6. Run the dashboard
```bash
cd frontend
npm install
npm run dev
```
Visit `http://localhost:3000`.

### 7. Expose your webhook (local dev only)
```bash
python -c "from pyngrok import ngrok; t = ngrok.connect(8000); print(t.public_url); input()"
```
In your Meta app's WhatsApp → Configuration page, set the webhook Callback URL to `<ngrok-url>/webhook/whatsapp`, enter your `META_VERIFY_TOKEN`, verify, and subscribe to the `messages` field.

---

## Testing without WhatsApp

Talk to the agent directly via terminal, no Meta setup required:
```bash
python -m app.agent.loop
```

Or via HTTP:
```bash
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"phone_number": "+10000000000", "message": "what tours are available"}'
```

---

## Known limitations / roadmap

- **Meta access token is temporary (~24h).** Needs a long-lived System User token before any real deployment.
- **No Redis queue or webhook idempotency yet** — a duplicate webhook delivery from Meta would currently be processed twice.
- **No receipt upload/OCR.** Payment verification is currently a manual human judgment call via the dashboard (checking the real bank account off-screen), not an automated receipt-matching pipeline.
- **Not yet deployed.** Currently runs locally with ngrok tunneling; Railway/Fly.io are the planned first deployment targets, with Neon/Supabase for managed Postgres.
- **No WhatsApp message templates.** Outbound messages outside the 24-hour customer service window (e.g. marketing to past customers) require Meta-approved templates, which aren't set up yet.
