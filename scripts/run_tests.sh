#!/bin/bash
# Quick test runner for Vecinita
# Bypasses uv run which may have venv issues

TEST_FILE="${1:-tests/}"
VERBOSE="${2:--}"
COVERAGE="${3:--}"

ARGS=("--tb=short")

if [[ "$VERBOSE" == "-v" || "$VERBOSE" == "--verbose" ]]; then
    ARGS+=("-v")
fi

if [[ "$COVERAGE" == "-c" || "$COVERAGE" == "--coverage" ]]; then
    ARGS+=("--cov=src" "--cov-report=term-missing")
fi

ARGS+=("$TEST_FILE")

echo "Running pytest with args: ${ARGS[@]}"
python -m pytest "${ARGS[@]}"

if [ $? -eq 0 ]; then
    echo "✓ All tests passed!"
else
    echo "✗ Tests failed with exit code: $?"
fi
