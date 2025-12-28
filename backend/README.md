# Vecinita Backend (FastAPI)

This backend container builds from the repository root using `backend/Dockerfile`, copying the Python package sources from `src/`, along with `scripts/` and `tests/`.

## Build & Run (Compose)

From the repo root:

```bash
docker compose up --build
```

- Backend: http://localhost:8000
- Healthcheck: http://localhost:8000/health

## Notes
- Dockerfile uses Playwright Python base to support scraping and browser automation.
- Dependencies install via `pyproject.toml` with the `embedding` extra.
- App entrypoint: `uvicorn src.agent.main:app --host 0.0.0.0 --port 8000`.
- If you later move `src/`, `scripts/`, and `tests/` into `backend/`, you can change the compose build `context` to `./backend` and keep the same Dockerfile.
