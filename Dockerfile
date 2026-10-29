# ==================================================
# GENEDXPLORER DOCKERFILE
# Multi-stage production container build
# ==================================================

# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
ENV VITE_API_BASE_URL=""
RUN npm run build

# Stage 2: Python Backend Runtime
FROM python:3.12-slim AS runner
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY src/ ./src/
COPY api.py ./
COPY main.py ./
COPY .env.example ./

# Copy compiled static frontend build from Stage 1 into static folder
COPY --from=frontend-builder /app/frontend/dist /app/static

# Create results output directory
RUN mkdir -p /app/results

# Default environment settings
ENV PORT=8000
ENV HOST=0.0.0.0
ENV LOG_LEVEL=INFO
ENV STATIC_DIR=/app/static

EXPOSE 8000

# Run FastAPI backend via Uvicorn
CMD ["python3", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
