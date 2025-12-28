# Use an official Python runtime as a parent image
# Use official Playwright Python image if browsers are needed
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

# Set the working directory in the container
WORKDIR /app

# Note: This root Dockerfile is kept for convenience builds.
# The canonical backend Dockerfile lives in ./backend/Dockerfile and is used by docker-compose.
# Copy backend Python project manifest for dependency installation
COPY backend/pyproject.toml ./

# Copy backend source code needed for package installation
COPY backend/src/ ./src/
COPY backend/scripts/ ./scripts/
COPY backend/tests/ ./tests/

# Install system dependencies required for building packages (graphviz, build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    graphviz \
    graphviz-dev \
    pkg-config

# Install any needed packages specified in pyproject.toml
ENV PYTHONUNBUFFERED=1
ENV TF_ENABLE_ONEDNN_OPTS=0
RUN pip install --no-cache-dir --upgrade pip
# Install the package with only embedding optional dependency (skip dev and visualization to reduce size and network issues)
# Visualization/pygraphviz pulls huge CUDA libraries that cause SSL download failures
RUN pip install --no-cache-dir --retries 5 --default-timeout=1000 ".[embedding]"

# Clean up apt cache after all builds are complete
RUN rm -rf /var/lib/apt/lists/*

# Pre-cache embedding model to speed up first run (optional)
# Align with default used in app (all-MiniLM-L6-v2)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')" || true

# Ensure Playwright browsers are installed
RUN playwright install --with-deps

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "src.agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
