# Vecinita Frontend (Vite + Tailwind + shadcn)

This is a React (JavaScript) frontend scaffolded with Vite, Tailwind CSS, and shadcn-style components. It provides a simple UI to query the Vecinita backend (`/ask`) and display answers with source links.

## Scripts

```bash
# Dev (on host)
npm install
npm run dev

# Build
npm run build

# Preview static build
npm run preview
```

## Docker

Build and run both services together:

```bash
# From repo root
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend:  http://localhost:8000

## Configuration

- The frontend reads `VITE_BACKEND_URL` (provided in docker-compose) and falls back to `http://localhost:8000` for local dev.
- Tailwind tokens are defined with CSS variables compatible with shadcn/ui.

## Notes

- `components.json` is included to support shadcn/ui CLI installs later if desired.
- Add more shadcn components under `src/components/ui/` as needed.

## Chat Widget

- A floating chat widget is available and mounted in the app. It appears at the bottom-right with a language selector (Español/English).
- It calls the backend `/ask` endpoint and passes `lang=es|en`. For local dev, the Vite proxy forwards `/api/*` to `http://localhost:8000`.
- Set `VITE_BACKEND_URL` to the backend base if you prefer direct calls (e.g., when not using the dev proxy). The widget will use that base when provided.

### Dev Tips

```bash
# Run backend (FastAPI) on 8000 separately
uv run -m uvicorn src.main:app --reload --port 8000

# Run frontend with proxy
npm run dev
```

### Features

- Fullscreen mode for the chat window
- Font size controls (A+/A−/Reset)
- Resource cards: Links and downloadable documents are shown as cards under assistant replies

