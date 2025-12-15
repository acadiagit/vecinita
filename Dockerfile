# Use an official Python runtime as a parent image
# Use official Playwright Python image if browsers are needed
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

# Set the working directory in the container
WORKDIR /app

# Copy pyproject.toml and README.md for dependency installation
COPY pyproject.toml README.md ./

# Copy source code needed for package installation
COPY src/ ./src/

# Install system dependencies required for building packages (graphviz, build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    graphviz \
    graphviz-dev \
    pkg-config

# Install any needed packages specified in pyproject.toml
ENV PYTHONUNBUFFERED=1
RUN pip install --no-cache-dir --upgrade pip
# Install the package with only embedding optional dependency (skip dev and visualization to reduce size and network issues)
# Visualization/pygraphviz pulls huge CUDA libraries that cause SSL download failures
RUN pip install --no-cache-dir --retries 5 --default-timeout=1000 ".[embedding]"

# Clean up apt cache after all builds are complete
RUN rm -rf /var/lib/apt/lists/*

# Pre-cache embedding model to speed up first run (optional)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')" || true

# Ensure Playwright browsers are installed
RUN playwright install --with-deps

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
