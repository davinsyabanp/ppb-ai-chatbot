# ----------- Stage 1: Builder -----------
    FROM python:3.11-slim-bookworm AS builder

    # Set environment variables for Python
    ENV PYTHONDONTWRITEBYTECODE=1 \
        PYTHONUNBUFFERED=1
    
    # Install build dependencies
    RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        && rm -rf /var/lib/apt/lists/*
    
    # Set working directory
    WORKDIR /app
    
    # Copy only requirements.txt first for better caching
    COPY requirements.txt .
    
    # Create a virtual environment and install dependencies
    RUN python -m venv /opt/venv \
        && /opt/venv/bin/pip install --upgrade pip \
        && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt
    
    # ----------- Stage 2: Final Image -----------
    FROM python:3.11-slim-bookworm
    
    # Set environment variables for Python and Cloud Run
    ENV PYTHONDONTWRITEBYTECODE=1 \
        PYTHONUNBUFFERED=1 \
        VIRTUAL_ENV=/opt/venv \
        PATH="/opt/venv/bin:$PATH" \
        PORT=8080
    
    # Create a non-root user and group
    RUN addgroup --system appuser && adduser --system --ingroup appuser appuser
    
    # Set working directory
    WORKDIR /app
    
    # Copy the virtual environment from the builder stage
    COPY --from=builder /opt/venv /opt/venv
    
    # Copy application source code and data directory
    COPY . /app
    
    # Change ownership to the non-root user
    RUN chown -R appuser:appuser /app
    
    # Switch to non-root user
    USER appuser
    
    # Expose the port (for documentation; Cloud Run uses $PORT)
    EXPOSE 8080
    
    # Start the Flask app using Gunicorn, binding to 0.0.0.0 and $PORT, with 4 workers
    # 'main:app' points to the Flask app instance in main.py
    CMD ["/bin/sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers 4 main:app"]