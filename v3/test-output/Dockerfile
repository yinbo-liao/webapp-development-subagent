# Multi-stage build for production
FROM python:3.11-slim as builder

# Security: Run as non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends     gcc     postgresql-client     && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Security: Copy non-root user from builder
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends     postgresql-client     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appgroup . .

# Security: Switch to non-root user
USER appuser

# Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3     CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
