# Minimal container for running Pluto tests in a clean environment
FROM python:3.12-slim

WORKDIR /app

# Install system deps for common Python packages and testing tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy repository
COPY . /app

# Default command: run test suite for agents
CMD ["bash", "-lc", "pytest -q agents --maxfail=1"]
