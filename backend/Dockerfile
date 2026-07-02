# Build stage using official Python alpine base image for compactness and security.
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies needed for compiling postgres drivers or utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source files
COPY . .

# Expose backend REST API port
EXPOSE 8000

# Run alembic migrations, database seeding, and start FastAPI via uvicorn
CMD ["sh", "-c", "alembic upgrade head && python -m app.utils.seeder && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
