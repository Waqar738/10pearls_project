FROM python:3.11-slim

WORKDIR /app

# Copy only backend requirements first (better layer caching)
COPY requirements_backend.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements_backend.txt

# Copy only necessary backend code
COPY app/ app/
COPY scripts/ scripts/
COPY Procfile .

CMD ["sh", "-c", "uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT}"]