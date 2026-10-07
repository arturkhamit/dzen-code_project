from django.core.validators import FileExtensionValidator
from django.db import models

# Keep this import available for the upload_to callable in migration 0003.
from comments.services.attachment_path import attachment_path


class CommentAttachment(models.Model):
    class Kind(models.TextChoices):
        IMAGE = "image", "Image"
        TEXT = "text", "Text file"

    comment = models.OneToOneField(
        "comments.Comment", on_delete=models.CASCADE, related_name="attachment",
    )
    file = models.FileField(
        upload_to=attachment_path,
        validators=[FileExtensionValidator(["jpg", "jpeg", "gif", "png", "txt"])],
    )
    original_name = models.CharField(max_length=255, blank=True, editable=False)
    kind = models.CharField(max_length=5, choices=Kind.choices, blank=True, editable=False)
    size = models.PositiveIntegerField(default=0, editable=False)
    width = models.PositiveSmallIntegerField(null=True, blank=True, editable=False)
    height = models.PositiveSmallIntegerField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Comment attachment"
        verbose_name_plural = "Comment attachments"

    def __str__(self):
        return self.original_name or self.file.name
