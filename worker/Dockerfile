FROM python:3.12-slim AS base
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    ca-certificates \
  && TRIVY_VERSION=$(curl -s https://api.github.com/repos/aquasecurity/trivy/releases/latest | grep '"tag_name"' | cut -d'"' -f4 | sed 's/v//') \
  && wget -qO /tmp/trivy.tar.gz "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz" \
  && tar -xzf /tmp/trivy.tar.gz -C /usr/local/bin trivy \
  && rm /tmp/trivy.tar.gz \
  && apt-get remove -y wget && apt-get autoremove -y \
  && rm -rf /var/lib/apt/lists/*

# Pre-download Trivy vulnerability DB so no network needed at scan time
RUN mkdir -p /trivy-cache && chmod 777 /trivy-cache
ENV TRIVY_CACHE_DIR=/trivy-cache
RUN trivy image --download-db-only --cache-dir /trivy-cache

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
