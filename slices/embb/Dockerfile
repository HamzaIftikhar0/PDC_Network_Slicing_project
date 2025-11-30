FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Upgrade pip + install deps
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Now copy the rest of your slice code
COPY . .

EXPOSE 5010

CMD ["python", "main.py"]
