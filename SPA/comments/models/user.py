from django.core.validators import RegexValidator, URLValidator
from django.db import models


class CommentAuthor(models.Model):
    username = models.CharField(
        max_length=80,
        validators=[RegexValidator(r"\A[A-Za-z0-9]+\Z", "Use Latin letters and digits only.")],
    )
    email = models.EmailField(max_length=254)
    homepage = models.URLField(
        max_length=2048, blank=True, validators=[URLValidator(schemes=["http", "https"])],
    )
    avatar_url = models.URLField(
        max_length=2048, blank=True, validators=[URLValidator(schemes=["http", "https"])],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Comment author"
        verbose_name_plural = "Comment authors"
        constraints = [
            models.UniqueConstraint(fields=["username", "email"], name="comments_author_identity"),
        ]

    def __str__(self):
        return self.username
