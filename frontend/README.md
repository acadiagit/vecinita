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
