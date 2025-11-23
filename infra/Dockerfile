# infra/Dockerfile
FROM python:3.11-slim

# system deps
RUN apt-get update && apt-get install -y build-essential git gcc ffmpeg libsndfile1 curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copy Python requirements then install
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

# copy app
COPY . /app

# create folder for runtime data
RUN mkdir -p /app/runtime /app/logs /app/models /app/data

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PYTHONPATH=/app

# entrypoint runs the FastAPI server on port 8080
CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "120"]
