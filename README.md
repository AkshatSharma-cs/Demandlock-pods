# DemandLock Pods

Open-source, offline-first PWA for rural India: local employers voice-note a need,
AI drafts a ticket, rules open a teacher-run learning pod once demand is real,
and outcomes are tracked.

Citi Ada Lovelace Hackathon 2026.

Live mode is the default Docker configuration. Demo data is explicitly opt-in.

## Structure

- `backend/` FastAPI app, services, seed data, and tests
- `frontend/` React PWA (pages, i18n, and offline outbox)
- `docs/` architecture, OpenAPI plan, demo script, and team workflow

## Run with Docker (live)

Copy `.env.example` to `.env`, set a strong `SECRET_KEY` and
`POSTGRES_PASSWORD`, then run:

```bash
docker compose up --build
```

Open http://localhost:8080. Register an employer, facilitator, or student from the
sign-in screen. Facilitators are unverified until an administrator runs:

```bash
docker compose exec api python scripts/verify_facilitator.py <phone>
```

Admin accounts cannot be self-registered. **Untested:** the first-admin provisioning
procedure for a production PostgreSQL deployment; provision the first admin through
the protected deployment/database process.

## Run demo

```bash
SEED_DEMO=true DEMO_MODE=true docker compose up --build
```

Demo mode enables simulated rows, the demo user switcher, and
`X-Demo-User-Id` authentication. Do not use it for a live deployment.

## Environment

| Variable | Default | Purpose |
| --- | --- | --- |
| `POSTGRES_PASSWORD` | `change-me` | PostgreSQL password; change for deployments |
| `SECRET_KEY` | `change-me` | HMAC signing key; use a long random value |
| `DEMO_MODE` | `false` in Compose | Enables demo authentication and UI |
| `SEED_DEMO` | `false` | Loads simulated demo rows |
| `CORS_ORIGINS` | `http://localhost:8080` | Comma-separated browser origins |
| `AUDIO_DIR` | `/app/media/audio` | Persistent audio upload directory |
| `POD_THRESHOLD` | `5` | Confirmed employment slots needed for a pod |

Compose supplies `DATABASE_URL` as
`postgresql+psycopg2://demandlock:${POSTGRES_PASSWORD}@db:5432/demandlock`.
The `.env` file is ignored by Git.

To reset the schema after model changes:

```bash
docker compose down -v
```

This is required once when upgrading an existing database because `create_all()`
does not alter existing tables.

## Without Docker (development)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
python backend/scripts/init_db.py
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

## Verification status

Tested: backend `pytest -q` (127 passed), frontend `npm test` (6 passed),
frontend `npm run build`, and `docker compose config`.

**Untested:** full Docker image startup and end-to-end browser registration flow
until the Docker image pull/build completes in the local environment.
