FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && adduser --system --group health \
    && mkdir -p data staticfiles \
    && chown health:health data staticfiles
COPY . .
USER health

EXPOSE 8000
