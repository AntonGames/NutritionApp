FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV NUTRITION_APP_ROOT=/app

WORKDIR /app

COPY pyproject.toml README.md ./
COPY config ./config
COPY src ./src

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "nutrition_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
