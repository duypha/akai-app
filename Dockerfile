# ─────────────────────────────────────────────────────────────
# Stage 1: Build React frontend
# ─────────────────────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend-react/package*.json ./
RUN npm ci --prefer-offline

COPY frontend-react/ ./
RUN npm run build

# ─────────────────────────────────────────────────────────────
# Stage 2: Python backend (serves built React + API + WebSocket)
# ─────────────────────────────────────────────────────────────
FROM python:3.11-slim

# ffmpeg is required by pydub for audio processing
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy React build from stage 1
# Path must mirror what main.py expects:
#   os.path.dirname(__file__) = /app/backend/app
#   ../../frontend-react/build  = /app/frontend-react/build
COPY --from=frontend-builder /frontend/build ./frontend-react/build/

# Persistent directory for SQLite database
RUN mkdir -p ./backend/data

EXPOSE 8000

WORKDIR /app/backend

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
