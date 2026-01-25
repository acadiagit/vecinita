#!/usr/bin/env bash
set -euo pipefail

# This script sets GitHub repository secrets using GitHub CLI without echoing values.
# It reads values from the local .env file where available and prompts for sensitive tokens.

ROOT_DIR="$(cd "$(dirname "$0")"/../.. && pwd)"
cd "$ROOT_DIR"

echo "Checking GitHub CLI authentication..."
if ! gh auth status >/dev/null 2>&1; then
  echo "Error: GitHub CLI is not authenticated. Run 'gh auth login' first." >&2
  exit 1
fi

REPO_NAME=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)
if [[ -z "$REPO_NAME" ]]; then
  echo "Error: Unable to determine repository. Ensure you're inside a Git repo and 'gh' is authenticated." >&2
  exit 1
fi
echo "Using repository: $REPO_NAME"

ENV_FILE=".env"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Warning: $ENV_FILE not found; will skip ENV-based secrets."
else
  echo "Reading $ENV_FILE for secrets..."
fi

get_env() {
  local key="$1"
  if [[ -f "$ENV_FILE" ]]; then
    # Extract key=value ignoring comments and blank lines
    awk -v k="$key" -F '=' 'BEGIN{IGNORECASE=0} $1==k {print substr($0, index($0,$2))}' "$ENV_FILE"
  fi
}

set_secret_if_present() {
  local name="$1"
  local value="$2"
  if [[ -n "$value" ]]; then
    printf "%s" "$value" | gh secret set "$name" -b - >/dev/null
    echo "✓ Set secret: $name"
  else
    echo "- Skipped secret (missing): $name"
  fi
}

echo "Setting environment-based secrets (if present):"
SUPABASE_URL_VAL="$(get_env SUPABASE_URL || true)"
SUPABASE_KEY_VAL="$(get_env SUPABASE_KEY || true)"
GROQ_API_KEY_VAL="$(get_env GROQ_API_KEY || true)"

set_secret_if_present "SUPABASE_URL" "$SUPABASE_URL_VAL"
set_secret_if_present "SUPABASE_KEY" "$SUPABASE_KEY_VAL"
set_secret_if_present "GROQ_API_KEY" "$GROQ_API_KEY_VAL"

echo
echo "Prompting for GitHub Personal Access Token (GH_TOKEN)..."
read -r -s -p "Enter GH_TOKEN (input hidden): " GH_TOKEN_INPUT
echo
if [[ -n "$GH_TOKEN_INPUT" ]]; then
  printf "%s" "$GH_TOKEN_INPUT" | gh secret set GH_TOKEN -b - >/dev/null
  echo "✓ Set secret: GH_TOKEN"
else
  echo "- Skipped secret: GH_TOKEN (no input)"
fi

echo
echo "All done. Repository secrets are configured without exposing values."
