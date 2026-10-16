# DemandLock Pods

Open-source, offline-first PWA for rural India: local employers voice-note a need,
AI drafts a ticket, rules open a teacher-run learning pod once demand is real,
and outcomes are tracked.

Citi Ada Lovelace Hackathon 2026.

> Demo data is SIMULATED unless stated otherwise.

## Structure
- backend/   FastAPI app, services (extractor, retrieval, safeguarding), seed data, tests
- frontend/  React PWA (pages, i18n, offline outbox)
- docs/      architecture, OpenAPI plan, demo script, team workflow

## Run

### Docker

```bash
docker compose up --build
```

Open http://localhost:8080.

### Without Docker

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
python backend/seed/seed_demo.py
uvicorn app.main:app --app-dir backend --port 8000
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Phones need HTTPS for microphone access; try
`cloudflared tunnel --url http://localhost:5173` for a local tunnel.
