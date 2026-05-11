FROM python:3.12-slim AS base
WORKDIR /app

ENV TRIVY_VERSION=0.61.0
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
  && curl -sL "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz" \
     -o /tmp/trivy.tar.gz \
  && tar -xzf /tmp/trivy.tar.gz -C /usr/local/bin trivy \
  && rm /tmp/trivy.tar.gz \
  && rm -rf /var/lib/apt/lists/*

# Pre-download Trivy vulnerability DB into /trivy-cache
# --cache-dir is a global flag and must come before the subcommand
RUN mkdir -p /trivy-cache && chmod 777 /trivy-cache
ENV TRIVY_CACHE_DIR=/trivy-cache
RUN trivy --cache-dir /trivy-cache image --download-db-only

COPY requirements.txt .

FROM base AS development
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-m", "app.main"]

FROM base AS production
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -r -u 1001 -d /home/workeruser -m workeruser && \
    chown -R workeruser:workeruser /trivy-cache
USER workeruser
CMD ["python", "-m", "app.main"]
