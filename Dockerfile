FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

COPY ./reqs/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src .
COPY ./pyproject.toml .
COPY ./README.md .
RUN pip install --no-cache-dir .
ENV PYTHONPATH=/app
EXPOSE 8000
