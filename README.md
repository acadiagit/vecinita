# vecinita

![Tests](https://github.com/acadiagit/vecinita/actions/workflows/test.yml/badge.svg)
![Codecov](https://codecov.io/gh/acadiagit/vecinita/branch/main/graph/badge.svg)
![Python Versions](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue)
![OS: Windows](https://img.shields.io/badge/OS-Windows-success)
![OS: Ubuntu](https://img.shields.io/badge/OS-Ubuntu-success)

VECINA assistant

## Project Structure

After refactoring, the project follows this structure:

```
vecinita/
├── src/
│   ├── main.py              # FastAPI application entry point
│   ├── static/
│   │   └── index.html       # Web UI
│   └── utils/
│       ├── faq_loader.py
│       ├── load_faq.py
│       ├── scraper_to_text.py
│       ├── supabase_db_test.py
│       └── vector_loader.py
├── scripts/
│   └── data_scrape_load.sh  # Data pipeline orchestrator script
├── tests/                   # Test files
├── data/                    # Data files and documents
├── docs/                    # Documentation
└── ...
```

## Key Changes

- **main.py**: Moved to `src/main.py`
- **index.html**: Moved to `src/static/index.html`
- **utils/**: Moved to `src/utils/`
- **data_scrape_load.sh**: Moved to `scripts/data_scrape_load.sh`

## Running the Application

### Using uvicorn directly

```bash
cd src
uvicorn main:app --reload
```

### Using uv

```bash
uv run -m uvicorn src.main:app --reload
```

Or, if you prefer to sync dependencies first and then run:

```bash
uv sync
uv run -m uvicorn src.main:app --reload
```

### Using Docker

Build and run the Docker container:

```bash
docker build -t vecinita .
docker run -p 8000:8000 vecinita
```

### Using Docker Compose

Run the application with Docker Compose:

```bash
docker-compose up
```

To run in the background:

```bash
docker-compose up -d
```

To stop and remove containers:

```bash
docker-compose down
```

# Test commit Tue Dec  2 22:14:49 UTC 2025
