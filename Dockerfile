FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=SPA.settings.production \
    STATIC_ROOT=/srv/static \
    MEDIA_ROOT=/srv/media

WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home app

COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir .
COPY SPA/ ./SPA/
COPY --from=frontend /app/SPA/comments/static/comments/dist/ ./SPA/comments/static/comments/dist/
COPY --chmod=755 deploy/entrypoint.sh /app/deploy/entrypoint.sh
RUN mkdir -p /srv/static /srv/media && chown -R app:app /srv/static /srv/media
USER app
WORKDIR /app/SPA
EXPOSE 8002
ENTRYPOINT ["/app/deploy/entrypoint.sh"]

CMD ["uvicorn", "SPA.asgi:application", "--host", "0.0.0.0", "--port", "8002", "--workers", "2", "--no-proxy-headers"]
