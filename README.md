# PrePora

PrePora is a mobile-first exam preparation workspace for Class 12 students preparing for CBSE Boards, NEET-UG, CUET-UG and AIIMS Nursing.

## Current implementation

The repository now contains a working React/Vite student experience with:

- Product landing page and responsive app shell.
- Light/dark theme switching.
- Student overview dashboard with activity, focus tasks and subject pulse.
- Practice lab with recommended tests and custom test builder.
- Functional test-taking flow, answer selection, navigation and result screen.
- Analytics page with score trend, chapter mastery and subject breakdown.
- Adaptive study planner with persistent-in-session task completion.
- Mistake notebook and AI tutor workflow.
- FastAPI foundation with health, exam catalog, test-generation, JWT auth and per-user progress endpoints.
- SQLite-backed account persistence for local development: each email receives an isolated profile, dashboard and test-attempt history.
- Complete 94-chapter content catalog with searchable formula, reaction and NCERT recall cards served by the API when available.
- Server-backed test sessions with live expiry, answer persistence, mark-for-review state and idempotent submit behaviour.
- Mistakes automatically create Smart Queue items; planner items can be added and completed per account.
- Analytics endpoint reports attempt trend, best/average score, open review work and a next-best recommendation.
- Tutor endpoint provides chapter-aware explanations, quiz prompts and revision plans with a local fallback.
- Ask from Photo validates JPG/PNG/WEBP uploads and accepts typed question context for a grounded solution path; OCR is intentionally not guessed without a configured vision provider.
- Workspace search now queries the chapter/reference catalog, and profile settings persist the target exam for the signed-in account.
- Security response headers, production JWT-secret validation and backend core tests are included.

Demo content is intentionally labelled in the API. It must be replaced with approved/licensed question-bank data before production use.

## Run locally

```bash
npm install --prefix frontend
npm run dev
```

The frontend runs at `http://localhost:5173`.

When the API is running, the login screen creates a first account on the first successful email/password submission and logs existing accounts in. If the API is unavailable, the frontend keeps a local-only fallback so the UI remains usable.

To run the API:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Copy `backend/.env.example` to `backend/.env` and replace secrets before enabling integrations.

Useful API routes include `POST /api/auth/signup`, `POST /api/auth/login`, `GET /api/auth/me`, `GET /api/dashboard`, `PATCH /api/profile`, `GET /api/content/chapters`, `GET /api/content/references`, `POST /api/progress/events`, `POST /api/tests/sessions`, `PATCH /api/tests/sessions/{id}/answer`, `POST /api/tests/sessions/{id}/submit`, `GET /api/study/items`, `POST /api/study/items`, `POST /api/study/items/{id}/complete`, `GET /api/analytics`, and `POST /api/tutor/respond`. Set `VITE_API_URL` when the API is hosted somewhere other than `http://127.0.0.1:8000`.

To run the backend checks:

```bash
backend/.venv/bin/python -m unittest backend.tests.test_core -v
```

## Deploy the frontend to Vercel

Import the repository into Vercel and set the project root directory to
`frontend`. Use `npm run build` as the build command and `dist` as the output
directory. Set `VITE_API_URL` to the public URL of the deployed FastAPI API,
then redeploy. The frontend includes a SPA rewrite in `frontend/vercel.json`
so direct refreshes keep working.

The current SQLite adapter is for local/demo development. A production API
needs a persistent database service and the SQLite adapter must be migrated to
PostgreSQL before relying on hosted accounts or progress data.

For a local container run, use `docker compose up`. Before production, replace `JWT_SECRET`, restrict `FRONTEND_ORIGIN`, configure a real database/backup policy, and connect an approved vision/AI provider.

## Roadmap

The next production slices are PostgreSQL/Alembic migration from the local SQLite adapter, RBAC, authoritative exam sessions, question-bank import/review, provider-independent AI streaming, RAG with approved sources, and real-time voice sessions. Credentials for those external services are intentionally not included.

## Four-area expansion

The current demo also includes four-area navigation: Learn, Practice, Improve and Plan. Learn contains the searchable Formula & Reactions Bank, NCERT library cards and Ask from Photo setup state. Practice contains the interactive Daily Challenge, verified-paper-only Previous Year Papers catalogue and custom test builder. Improve contains the weakness heatmap, mistake notebook and transparent score predictor. Plan contains the Smart Revision Queue, Revision Center and study planner.

Demo content is intentionally labelled in the UI and API. Ask from Photo does not simulate vision recognition; it shows an honest provider-not-configured state until a vision AI integration is supplied.
