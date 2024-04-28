FROM python:3.12
WORKDIR /code

COPY requirements.txt /code/requirements.txt
COPY pyproject.toml /code/pyproject.toml
COPY README.md /code/README.md

COPY src /code/src
# COPY server /code/server # docker-compose

RUN pip install --no-cache-dir --upgrade pip && pip install -e .

CMD ["uvicorn", "src.gurupod.__init__:app", "--host", "0.0.0.0"]
