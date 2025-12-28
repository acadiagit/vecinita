# Backend Dockerfile (Vecinita FastAPI + Playwright Python)

# Use official Playwright Python image (includes browsers)
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

# Set the working directory in the container
WORKDIR /app

# Copy backend Python project manifest
COPY pyproject.toml ./

# Copy source code and supporting folders from backend context
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY tests/ ./tests/

# Install system dependencies required for building packages
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	graphviz \
	graphviz-dev \
	pkg-config && \
	rm -rf /var/lib/apt/lists/*

# Python env flags
ENV PYTHONUNBUFFERED=1
ENV TF_ENABLE_ONEDNN_OPTS=0

# Upgrade pip and install package with embedding extra
RUN pip install --no-cache-dir --upgrade pip && \
	pip install --no-cache-dir --retries 5 --default-timeout=1000 ".[embedding]"

# Pre-cache embedding model to speed up first run (optional)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-mpnet-base-v2')" || true

# Ensure Playwright browsers are installed
RUN playwright install --with-deps

# Expose the FastAPI port
EXPOSE 8000

# Start the FastAPI app via uvicorn (module path: src.agent.main:app)
CMD ["uvicorn", "src.agent.main:app", "--host", "0.0.0.0", "--port", "8000"]