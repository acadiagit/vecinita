#!/bin/bash
# FastAPI development server runner for Vecinita
# Bypasses uv run which may have venv issues

PORT="${1:-8000}"
HOST="${2:-0.0.0.0}"

echo "Starting Vecinita FastAPI server..."
echo "API will be available at http://localhost:$PORT"
echo "Press Ctrl+C to stop"

python -m uvicorn src.main:app --reload --host $HOST --port $PORT

if [ $? -ne 0 ]; then
    echo "Server exited with code: $?"
fi
