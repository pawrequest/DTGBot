FROM python:3.12-slim

WORKDIR /app

COPY ./reqs/requirements.txt .
RUN apt-get update && apt-get install -y git
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src .
COPY ./pyproject.toml .
COPY ./README.md .
RUN pip install --no-cache-dir .

# Set the default command for the image
# It’s better to not define CMD here if you want to use the same image for different purposes
