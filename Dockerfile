FROM python:3.11-slim

WORKDIR /telegrambot

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false

RUN poetry install --no-interaction --no-root

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]