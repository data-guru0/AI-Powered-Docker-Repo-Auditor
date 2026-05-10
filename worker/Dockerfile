FROM python:3.12-slim AS base
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .

FROM base AS development
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-m", "app.main"]

FROM base AS production
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -r -u 1001 workeruser
USER workeruser
CMD ["python", "-m", "app.main"]
