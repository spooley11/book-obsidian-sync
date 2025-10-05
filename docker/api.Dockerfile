FROM python:3.11-slim

WORKDIR /app

ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VERSION=1.8.2

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

COPY apps/api/pyproject.toml apps/api/poetry.lock* ./apps/api/
RUN cd apps/api && poetry install --no-root --no-interaction

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
