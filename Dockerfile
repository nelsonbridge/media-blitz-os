# syntax=docker/dockerfile:1
FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/nelsonbridge/media-blitz-os"
LABEL org.opencontainers.image.title="nks"
LABEL org.opencontainers.image.description="Nelson Knowledge System portable runtime"

WORKDIR /app

# Build-time identity metadata injected by the governed publish workflow.
# Defaults are empty strings so the image can be built locally without them.
ARG NKS_GIT_COMMIT=""
ARG NKS_RELEASE_ID=""
ARG NKS_BUILD_TIMESTAMP=""

ENV NKS_GIT_COMMIT=${NKS_GIT_COMMIT} \
    NKS_RELEASE_ID=${NKS_RELEASE_ID} \
    NKS_BUILD_TIMESTAMP=${NKS_BUILD_TIMESTAMP}

# NKS_ENVIRONMENT is injected at deploy time, not build time.
# PORT is set by Cloud Run; default matches Cloud Run convention.
ENV PORT=8080

# Install the package. No test extras — the test suite runs in CI before build.
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

# Non-root runtime user.
RUN adduser --system --no-create-home --group nks

USER nks

EXPOSE 8080

ENTRYPOINT ["python", "-m", "nks.application.container_runtime"]
