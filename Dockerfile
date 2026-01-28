# Use an official Python runtime as a parent image
# Use official Playwright Python image if browsers are needed
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

# Set the working directory in the container
WORKDIR /app

# Copy pyproject.toml and README.md for dependency installation
COPY pyproject.toml README.md ./

# Copy source code needed for package installation
# This WILL include src/agent/static (frontend) and src/agent/data (rules)
COPY src/ ./src/

# --- NEW: Copy the data directory ---
# This ensures urls.txt and extracted_links.txt are available to the bot
COPY data/ ./data/

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
# Install the package with only embedding optional dependency
RUN pip install --no-cache-dir --retries 5 --default-timeout=1000 ".[embedding]"

# Clean up apt cache after all builds are complete
RUN rm -rf /var/lib/apt/lists/*

# --- UPDATED: Pre-cache the correct model ---
# Changed to all-MiniLM-L6-v2 to match what your main.py is actually using
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')" || true

# Ensure Playwright browsers are installed
RUN playwright install --with-deps

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "src.agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
