# Backend Dockerfile (Vecinita FastAPI Agent - Optimized for Production)
# This builds the Q&A agent without Playwright for faster builds and smaller images
# For scraping with Playwright, see Dockerfile.scraper

# Use slim Python image for production
FROM python:3.11-slim-bookworm

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
	curl \
	pkg-config && \
	rm -rf /var/lib/apt/lists/*

# Python env flags
ENV PYTHONUNBUFFERED=1
ENV TF_ENABLE_ONEDNN_OPTS=0

# Upgrade pip and install package with ONLY embedding extra (not scraping)
# This excludes Playwright and Unstructured, reducing image size and build time
RUN pip install --no-cache-dir --upgrade pip && \
	pip install --no-cache-dir --retries 5 --default-timeout=1000 ".[embedding]"

# Pre-cache embedding model to speed up first run
# Align with default used in app (all-MiniLM-L6-v2)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')" || true

# Expose the FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=5 \
	CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start the FastAPI app via uvicorn (module path: src.agent.main:app)
# Use PORT env var (default 8000 for local dev, 10000 for Render)
# Add graceful shutdown timeout to prevent hanging deploys
CMD ["sh", "-c", "uvicorn src.agent.main:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-graceful-shutdown 30"]