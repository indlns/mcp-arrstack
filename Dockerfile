# ──────────────────────────────────────────────
# MCP ARR Stack — Dockerfile
# Multi-stage build for minimal production image
# ──────────────────────────────────────────────

# ── Stage 1: Build ─────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Production ────────────────────────
FROM python:3.12-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

# Create non-root user
RUN groupadd --system --gid 1000 mcpuser && \
    useradd --system --uid 1000 --gid 1000 --create-home mcpuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY --chown=mcpuser:mcpuser src/ ./src/
COPY --chown=mcpuser:mcpuser pyproject.toml ./
COPY --chown=mcpuser:mcpuser tests/ ./tests/

# Switch to non-root user
USER mcpuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Expose port for HTTP transport (8080)
# Note: stdio transport does not use this port
EXPOSE 8080

# Default transport: stdio. Override with environment variable:
#   MCP_TRANSPORT=http  → enables Streamable HTTP on port 8080
ENV MCP_TRANSPORT=stdio

# Run the MCP server
CMD ["python", "-m", "src.server"]
