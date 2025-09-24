FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements ./requirements
RUN pip install --no-cache-dir -r requirements/frontend.txt

COPY src ./src

ENV PYTHONPATH=/app/src \
    PORT=3000

EXPOSE 3000

CMD ["uvicorn", "starlite_app:create_app", "--factory", "--host", "0.0.0.0", "--port", "3000"]
