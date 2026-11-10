# InterviewIQ — Your Personal AI Interviewer

A platform where you practice real job interviews against an AI that **adapts to your answers** and
**remembers how you've grown** across sessions.

## The idea

You pick a target job (Frontend, Backend, Full Stack, DevOps…), your experience level, an interview
type, and optionally a company/technology. The AI becomes your interviewer:

- It asks **one question at a time** and reacts to your previous answer (probe a gap, or go harder).
- **Difficulty adapts**: strong answers raise it, weak ones lower it (`services/interviewer.py`).
- Every answer is scored on **technical accuracy, communication, reasoning, completeness, problem-solving**.
- At the end you get a report; your per-skill scores are saved to **Interview Memory**.

### The special feature: Interview Memory & Candidate Intelligence

Most simulators score each interview in isolation. InterviewIQ stores a `SkillScore` per skill per
interview, then compares your latest result with your earlier average:

> "You have improved in sql (+1.8 vs your earlier average). Query optimization remains an area to practice (latest 4.5/10)."

That memory is fed back into the interviewer, so the next interview probes your known weak spots, and a
one-click **practice session** is generated from your weakest skills.

## Features

| Feature | Where |
|---|---|
| Adaptive AI interviewer | `backend/app/services/interviewer.py` |
| Intelligent evaluation (5 criteria) + final report | `backend/app/services/evaluator.py` |
| Interview memory, trends, insights, practice sessions | `backend/app/services/memory.py` |
| Real-time interview over WebSockets | `backend/app/routers/ws.py`, `frontend/src/pages/InterviewRoom.tsx` |
| Live coding (Monaco editor + run button) | `InterviewRoom.tsx`, `backend/app/routers/code.py` |
| Voice interview (speak answers, hear questions) | `frontend/src/components/useSpeech.ts` |
| JWT auth | `backend/app/security.py`, `routers/auth.py` |
| Background report generation | `backend/app/worker.py` (Celery + Redis) |

## Tech stack

React + TypeScript · Tailwind CSS · Monaco Editor · FastAPI · PostgreSQL · SQLAlchemy · JWT ·
WebSockets · Celery + Redis · Anthropic API (LLM) · Browser Web Speech API (voice) · Docker

## Quick start (Docker)

```bash
cp .env.example .env        # optionally add ANTHROPIC_API_KEY
docker compose up --build
```

- App: http://localhost:5173
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health (shows whether the real LLM or the offline mock is active)

**No API key?** It still runs: a built-in mock interviewer and heuristic scorer keep the whole flow
usable for development. Add `ANTHROPIC_API_KEY` in `.env` for real adaptive questions and feedback.

## Run without Docker

```bash
# backend (SQLite, no Redis needed)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DATABASE_URL=sqlite:///./dev.db CELERY_EAGER=true uvicorn app.main:app --reload

# frontend
cd frontend
npm install
npm run dev
```

## Tests

```bash
cd backend && python -m pytest -q
```

Covers difficulty adaptation, memory insights, and a full register → interview (WebSocket) → report →
profile → code-run flow using the offline mock.

## How an interview flows

```
Browser ──REST──▶ POST /api/interviews            create + first question
Browser ◀─WS────▶ /ws/interviews/{id}             answer ─▶ evaluation + next question
Browser ──REST──▶ POST /api/interviews/{id}/finish  ─▶ Celery: report + memory update
Browser ──REST──▶ GET  /api/profile               skills, trends, insights
```

## Project layout

```
interviewiq/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── app/
│   │   ├── main.py  config.py  database.py  models.py  schemas.py  security.py  deps.py  worker.py
│   │   ├── routers/   auth · interviews · profile · code · ws
│   │   └── services/  llm · interviewer · evaluator · memory · session
│   └── tests/
└── frontend/
    └── src/
        ├── api.ts  App.tsx  main.tsx
        ├── components/useSpeech.ts
        └── pages/  Login · Dashboard · NewInterview · InterviewRoom · ReportPage · ProfilePage
```

## Before you deploy for real

- **Code execution is dev-only.** `routers/code.py` uses a resource-limited subprocess, which is *not* a
  security boundary. Run candidate code in an isolated sandbox (gVisor/Firecracker/Judge0) with no network.
- Set a strong `SECRET_KEY` (`openssl rand -hex 32`) and restrict `CORS_ORIGINS`.
- Replace `create_all` in `main.py` with Alembic migrations.
- Add rate limiting on the LLM-backed endpoints and WebSocket.
- Voice uses the browser's Web Speech API (best in Chrome/Edge). For production-quality voice, swap
  `useSpeech.ts` for cloud speech-to-text / text-to-speech.

## Roadmap ideas

1. Alembic migrations and OAuth2 social login (Google/GitHub)
2. Streaming LLM responses token-by-token over the WebSocket
3. Company-specific interview packs and a question bank with spaced repetition
4. Multi-language code execution and automated test cases per coding question
5. Progress charts, shareable reports, and interview history search
