FROM python:3.12-slim

# Install system dependencies and BUILD TOOLS for insightface
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip and install setuptools/wheel first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements.txt .

# Install dependencies (this will now be able to build the insightface wheel)
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "main:app"]
