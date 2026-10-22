# PrePora architecture

## Current repository shape

```text
frontend/   React + TypeScript + Vite student workspace
backend/    FastAPI API foundation and typed test-generation contract
docs/       Architecture and delivery notes
```

The frontend is intentionally organised around product surfaces rather than a single dashboard page: practice, analytics, planner, mistakes and tutor each have an independent view boundary. Login now prefers the authenticated FastAPI API and falls back to local-only mode when the API is not running, so the experience remains usable during local design work.

## Production data flow

```text
React client → authenticated FastAPI routes → SQLite adapter (local) → PostgreSQL adapter (production)
                                             ↘ Redis / background tasks
                                             ↘ provider-independent AI layer
```

The local API persists users, PBKDF2 password hashes, JWT sessions, dashboard progress, test attempts, resumable test sessions and per-user study items. A submitted test can create mistake and queue items from incorrect answers. The content service exposes the complete 94-chapter PCB taxonomy plus concise formula, reaction and NCERT recall cards. Analytics and tutor routes consume this account context. Demo mode is intentionally separate from authenticated account data.

Photo analysis validates uploads and can ground a response with user-supplied question text. It deliberately returns a setup state instead of inventing OCR when no vision provider is configured. Search uses the same content service, while settings write through the authenticated profile route.

The exam engine must keep the server authoritative for session expiry, scoring, and submission idempotency. The browser should only render the current server state and optimistically save answer changes.

## Integration boundaries still to wire

- PostgreSQL models and Alembic migrations for the existing users/progress/attempts tables plus question bank, mistakes and plans.
- Refresh-token rotation and server-side RBAC (the current local slice uses short-scope JWT access tokens).
- Production AI provider adapter, streaming responses and richer tutor citations (the current tutor is deterministic and content-aware by design).
- Vision/OCR provider adapter with encrypted object storage and retention controls.
- Question-bank CSV/JSON ingestion with verification state.
- Provider adapter for text streaming, structured generation and embeddings.
- Realtime voice session adapter with a text fallback.
- Background jobs for indexing and plan generation.

No production API key or copyrighted content is included in this repository.
