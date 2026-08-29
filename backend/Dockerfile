FROM python:3.12-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy backend, ML model, and lookup data
COPY backend/ ./backend/
COPY ml-model/ ./ml-model/
COPY disease_lookup.json .

# Run from the backend directory
WORKDIR /app/backend

# Use sh -c so that $PORT is evaluated at runtime (Render provides PORT env var)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
