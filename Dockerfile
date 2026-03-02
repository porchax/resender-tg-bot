FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY bot/ bot/
COPY alembic.ini .
COPY alembic/ alembic/

RUN pip install --upgrade pip && pip install --no-cache-dir .

CMD ["sh", "-c", "alembic upgrade head && python -m bot"]
