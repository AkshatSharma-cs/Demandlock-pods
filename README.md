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

For a presentation/demo, start the stack and open `http://localhost:8080`. The web
workspace includes the demand desk, learning pods, facilitator review, outcomes,
impact views, offline status, multilingual UI, and preloaded reference data. In live mode, register
an account first; the local Ollama and ASR features remain available through the
configured `.env` settings. (live)

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

### Presentation accounts

The following local accounts were created and login-tested for the prototype
demonstration:

| Role | Phone | PIN |
| --- | --- | --- |
| Employer | `9000000001` | `4826` |
| Student | `9000000002` | `5937` |
| Facilitator | `9000000003` | `7164` |

The facilitator account is verified and can demonstrate cohort review, task review,
module creation, and publishing. These are prototype-only credentials; change or
remove them before any shared, staging, or production deployment.

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
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Ollama API address |
| `OLLAMA_MODEL` | `qwen2.5:7b-instruct` | Local Ollama model |
| `WHISPER_MODEL` | `base.en` | Local faster-whisper model |

For the prototype, English voice input is recommended. The **Dictate** button uses
the browser SpeechRecognition service (Chrome/Edge, internet required) and fills an
editable transcript. The interface can be switched between English, Hindi, and
Tamil; the selected language also controls browser dictation where supported.
Recorded voice notes use local faster-whisper; set `WHISPER_MODEL=base.en` for
the faster English-only fallback. Typed input always remains available, and
extraction still requires explicit review and confirmation. Hindi/Tamil speech
accuracy remains subject to further evaluation.

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

Tested: backend `pytest -q` (128 passed), frontend `npm test` (9 passed),
frontend `npm run build`, `docker compose config`, Docker image build/start,
live health checks, live HTTP registration/login, and live smoke checks for the
facilitator cohort and outcomes workflows.

**Untested:** full browser automation beyond the documented live smoke checks,
testing on a real low-end Android device, and real employer confirmation.

## Blueprint scope

The current branch implements the blueprint's backend and browser workflows:
source-backed reference records, employer demand capture and human confirmation,
deterministic pods, safeguarding, facilitator review, module authoring, student
submissions, age-aware review permissions, pod-mode evaluation, published-module
attachment, verification-aware outcome recording, multilingual UI localization,
offline sync, and voice input/output fallbacks. Facilitators can evaluate
`supervised_practice` or `work_trial` pods and attach published modules. Adult
submissions can be reviewed by an employer or facilitator; minor submissions
are facilitator-only. Students record only `self_reported` outcomes, while
facilitators and employers record their respective confirmed verification levels.

The following blueprint items remain intentionally excluded at the request for this
implementation: a separate demo-mode redesign, testing on a real low-end Android
device, and obtaining real employer confirmations. Simulated data remains explicitly
labelled and no job, income, or placement guarantee is made.
