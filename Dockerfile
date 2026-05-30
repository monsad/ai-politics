# Multi-stage: build Next.js static export, then assemble Python runtime.

FROM node:20-bookworm-slim AS web-builder
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.11-slim-bookworm AS runtime
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PARLIAMENT_DB_PATH=/data/sessions.db \
    HERMES_YOLO_MODE=1 \
    HERMES_ACCEPT_HOOKS=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV CACHEBUST=2026-05-30T20-40-skills
COPY pyproject.toml README.md ./
COPY parliament/ ./parliament/
COPY skills/ ./skills/
COPY scripts/ ./scripts/
COPY deploy/ ./deploy/

RUN pip install --upgrade pip \
    && pip install -e .

# Hermes config + skills — both are looked up under ~/.hermes/ by the runtime
RUN mkdir -p /root/.hermes/skills \
    && cp deploy/hermes-config.yaml /root/.hermes/config.yaml \
    && cp -r skills/* /root/.hermes/skills/

# Static UI from the web-builder stage
COPY --from=web-builder /web/out/ ./web/out/

RUN mkdir -p /data

EXPOSE 8000
CMD ["sh", "deploy/entrypoint.sh"]
