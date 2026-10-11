from django.conf import settings
from django.core.validators import URLValidator
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    homepage = models.URLField(
        max_length=2048, blank=True, validators=[URLValidator(schemes=["http", "https"])],
    )
