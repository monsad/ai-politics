#!/bin/sh
set -e

# Write OpenRouter key (and any other Hermes-required keys) into ~/.hermes/.env
# so the hermes-agent subprocess picks them up via its own dotenv loader.
mkdir -p /root/.hermes
{
  if [ -n "${OPENROUTER_API_KEY}" ]; then echo "OPENROUTER_API_KEY=${OPENROUTER_API_KEY}"; fi
  if [ -n "${ANTHROPIC_API_KEY}" ]; then echo "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}"; fi
  if [ -n "${XAI_API_KEY}" ]; then echo "XAI_API_KEY=${XAI_API_KEY}"; fi
} > /root/.hermes/.env

exec uvicorn parliament.api:app --host 0.0.0.0 --port "${PORT:-8000}"
