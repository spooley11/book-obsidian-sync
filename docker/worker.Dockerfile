FROM python:3.11-slim

WORKDIR /app

ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VERSION=1.8.2

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

COPY apps/api/pyproject.toml apps/api/poetry.lock* ./apps/api/
COPY workers/pyproject.toml workers/poetry.lock* ./workers/
RUN cd apps/api && poetry install --no-root --no-interaction
RUN cd workers && poetry install --no-root --no-interaction

COPY . .

CMD ["celery", "-A", "workers.worker", "worker", "--loglevel=INFO"]
