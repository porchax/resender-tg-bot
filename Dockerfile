FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY alembic.ini .
COPY alembic/ alembic/
COPY bot/ bot/

CMD ["sh", "-c", "alembic upgrade head && python -m bot"]
