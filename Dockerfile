# ============================================================
# Multi-stage Dockerfile for the Chatbot application
# ============================================================

# Stage 1: Build the widget
FROM node:20-alpine AS widget-builder

WORKDIR /app/widget
COPY widget/package.json widget/package-lock.json* ./
RUN npm install
COPY widget/ ./
RUN npm run build

# Stage 2: Python application
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install .

# Copy application code
COPY backend/ ./backend/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Copy built widget from stage 1
COPY --from=widget-builder /app/widget/dist ./widget/dist

# Create non-root user
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser && \
    chown -R appuser:appgroup /app

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
