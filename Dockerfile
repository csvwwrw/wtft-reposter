FROM python:3.12-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

COPY requirements.txt ./

RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && playwright install --with-deps chromium

COPY . .

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app /ms-playwright

USER appuser

WORKDIR /app/src

CMD ["python", "main.py"]