FROM python:3.13-slim

WORKDIR /app

# Install system dependencies for DNS resolution
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p /app/output

# Expose FastAPI port
EXPOSE 8000

# Default: run the FastAPI server
CMD ["uvicorn", "omnilead.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
