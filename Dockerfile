FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    fluxbox \
    net-tools \
    procps \
    scrot \
    supervisor \
    websockify \
    wget \
    x11vnc \
    xauth \
    xdotool \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/novnc && \
    wget -qO- https://github.com/novnc/noVNC/archive/refs/tags/v1.5.0.tar.gz | tar xz --strip 1 -C /opt/novnc

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

RUN printf '%s\n' \
    '#!/bin/sh' \
    'set -e' \
    'Xvfb :1 -screen 0 1280x720x24 &' \
    'sleep 1' \
    'fluxbox >/tmp/fluxbox.log 2>&1 &' \
    'x11vnc -display :1 -forever -shared -nopw -listen 0.0.0.0 -rfbport 5900 >/tmp/x11vnc.log 2>&1 &' \
    'websockify --web=/opt/novnc 6080 localhost:5900 >/tmp/novnc.log 2>&1 &' \
    'python manage.py migrate --noinput' \
    'gunicorn alaha.wsgi:application --bind 0.0.0.0:8000' \
    > /start.sh && chmod +x /start.sh

EXPOSE 8000 6080 5900

CMD ["/start.sh"]
