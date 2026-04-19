FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV HOME=/codex-home

ARG TARGETARCH

RUN apt-get update \
    && apt-get install -y --no-install-recommends bubblewrap ca-certificates curl tar nodejs npm \
    && case "$TARGETARCH" in \
        amd64) CODEX_TARGET="x86_64-unknown-linux-musl" ;; \
        arm64) CODEX_TARGET="aarch64-unknown-linux-musl" ;; \
        *) echo "Unsupported architecture: $TARGETARCH" >&2; exit 1 ;; \
    esac \
    && curl -fsSL "https://github.com/openai/codex/releases/latest/download/codex-${CODEX_TARGET}.tar.gz" -o /tmp/codex.tar.gz \
    && tar -xzf /tmp/codex.tar.gz -C /tmp \
    && mv "/tmp/codex-${CODEX_TARGET}" /usr/local/bin/codex \
    && chmod +x /usr/local/bin/codex \
    && rm -f /tmp/codex.tar.gz \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /codex-home/.codex && chmod -R 0777 /codex-home

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
