FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
COPY requirements ./requirements
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY architecture/backend/start.sh ./start.sh
RUN chmod +x start.sh

ENV PYTHONPATH=/app/src \
    PORT=8001

EXPOSE 8001

ENTRYPOINT ["./start.sh"]
