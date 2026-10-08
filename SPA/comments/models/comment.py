from django.conf import settings
from django.core.validators import RegexValidator, URLValidator
from django.db import models
from django.utils import timezone

from comments.validators.entities import MAX_TEXT_LENGTH, validate_plain_text


class Comment(models.Model):
    author = models.ForeignKey(
        "comments.CommentAuthor", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="comments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="comments",
    )
    # Retain the contact details supplied with each post, even after a profile
    # changes or is removed. The author relation can group anonymous submissions.
    username = models.CharField(
        max_length=80, db_index=True,
        validators=[RegexValidator(r"\A[A-Za-z0-9]+\Z", "Use Latin letters and digits only.")],
    )
    email = models.EmailField(max_length=254, db_index=True)
    homepage = models.URLField(
        max_length=2048, blank=True, validators=[URLValidator(schemes=["http", "https"])],
    )
    avatar_url = models.URLField(
        max_length=2048, blank=True, validators=[URLValidator(schemes=["http", "https"])],
    )
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies",
    )
    quoted_comment = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="quoted_by",
    )
    text = models.TextField(max_length=MAX_TEXT_LENGTH, validators=[validate_plain_text])
    # Plain text and formatting ranges, using Telegram's UTF-16 offset convention.
    entities = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    # Expose this as read-only in a future serializer. Voting needs an authenticated
    # identity and an atomic update; a posted count is never a trusted vote.
    vote_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["parent", "created_at"], name="comments_co_parent__10bc81_idx"),
            models.Index(fields=["-created_at", "id"], name="comments_co_created_17a470_idx"),
        ]
        constraints = [
            models.CheckConstraint(condition=~models.Q(parent=models.F("id")), name="comments_no_self_reply"),
            models.CheckConstraint(condition=~models.Q(quoted_comment=models.F("id")), name="comments_no_self_quote"),
        ]

    def __str__(self):
        return f"{self.username}: {self.text[:60]}"
