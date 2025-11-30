FROM python:3.11-slim

WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .

# Install build tools + upgrade pip & installers, then install deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the scheduler code
COPY . .

EXPOSE 5000

CMD ["python", "generator.py"]
