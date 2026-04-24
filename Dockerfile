# Stage 1: Build the Vue frontend
FROM node:22-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Build and run the Python backend
FROM python:3.13-slim AS backend

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy workspace root files
COPY pyproject.toml uv.lock ./

# Copy workspace members
COPY engine/ engine/
COPY backend/ backend/

# Install dependencies (production only)
ENV UV_COMPILE_BYTECODE=1
RUN uv sync --frozen --no-dev --package backend

# Put the venv on PATH so uvicorn/python are found directly
ENV PATH="/app/.venv/bin:$PATH"

# Copy built frontend into a location the backend can serve
COPY --from=frontend-build /app/frontend/dist /app/static

EXPOSE 8080

CMD ["uvicorn", "chakes.backend.app:app", "--host", "0.0.0.0", "--port", "8080"]
