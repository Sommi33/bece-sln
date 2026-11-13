FROM python:3.12-slim

WORKDIR /app

# Create a non-root user for container security
RUN useradd -m appuser

# Install Python dependencies first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and switch to non-root user
COPY --chown=appuser:appuser . .
USER appuser

EXPOSE 5000

# Built-in container health check hitting your /api/health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

# Run with production Gunicorn server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
