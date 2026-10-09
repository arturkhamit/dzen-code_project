from pathlib import Path

from dotenv import load_dotenv

# Local settings read the project's .env regardless of the working directory.
# Production receives its environment from Docker Compose instead.
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

from .base import *


DEBUG = os.getenv("DEBUG", "1").lower() in {"1", "true", "yes"}
ALLOWED_HOSTS = [host.strip() for host in os.getenv(
    "ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]",
).split(",") if host.strip()]

# Print development emails locally; production keeps Django's SMTP default.
MAILERS = {
    "default": {"BACKEND": "django.core.mail.backends.console.EmailBackend"},
}
