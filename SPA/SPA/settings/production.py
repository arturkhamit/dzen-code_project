from django.core.exceptions import ImproperlyConfigured

from .base import *


DEBUG = False
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    raise ImproperlyConfigured("Set SECRET_KEY in the production environment.")

ALLOWED_HOSTS = [host.strip() for host in os.getenv(
    "ALLOWED_HOSTS", "dzen-code-comments.online",
).split(",") if host.strip()]
CSRF_TRUSTED_ORIGINS = ["https://dzen-code-comments.online"]

# The external Caddy sets this header; loopback-only Nginx passes it to Django.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# Keep HSTS scoped to this host until any other subdomains also support HTTPS.
SECURE_HSTS_SECONDS = 3600

# Nginx serves the collected assets and uploads from shared volumes.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
}
