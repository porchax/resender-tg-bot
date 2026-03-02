FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY bot/ bot/
COPY alembic.ini .
COPY alembic/ alembic/

RUN pip install --upgrade pip && pip install --no-cache-dir .

CMD ["sh", "-c", "alembic upgrade head && python -m bot"]
