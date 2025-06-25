FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir pyrogram requests

ENV PYTHONUNBUFFERED=1

CMD ["python", "Bot.py"] 