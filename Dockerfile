# Multi-stage Dockerfile for ThesisForge
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md ./
COPY src ./src

RUN uv pip install --system --no-cache-dir .

# Production Runner Stage
FROM python:3.12-slim AS runner

WORKDIR /app

# Security: Create non-root user
RUN groupadd -r thesisforge && useradd -r -g thesisforge thesisforge

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/thesisforge /usr/local/bin/thesisforge
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

COPY config.yaml.example ./config.yaml
COPY gui ./gui

RUN mkdir -p /app/data && chown -R thesisforge:thesisforge /app

USER thesisforge

ENV PORT=8000
ENV HOST=0.0.0.0
ENV ENVIRONMENT=production

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["thesisforge", "run", "--host", "0.0.0.0", "--port", "8000"]
