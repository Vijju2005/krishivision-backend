FROM python:3.10-slim

# Install system dependencies for OpenCV (gl1) and ReportLab
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

ENV DATABASE_URL="sqlite:///./krishivision.db"
ENV JWT_SECRET_KEY="production-secret-change-in-config"

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
