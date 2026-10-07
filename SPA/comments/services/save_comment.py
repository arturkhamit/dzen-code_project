import logging

from django.core.exceptions import ValidationError
from django.db import transaction

from comments.models import Comment

from .prepare_attachment import prepare_attachment
from .validate_comment import validate_comment


logger = logging.getLogger(__name__)


def save_comment(comment, *, upload=None):
    """Validate and save a comment and its optional new attachment together.

    The request layer must verify CAPTCHA and authorize any edit before calling
    this service. It owns the outer transaction so a later enclosing rollback
    cannot silently orphan an uploaded file. Do not wrap it in another atomic().
    """
    attachment = prepare_attachment(upload) if upload is not None else None
    original_pk, was_adding = comment.pk, comment._state.adding
    try:
        with transaction.atomic(durable=True):
            if not was_adding:
                # Lock before checking the stored parent and writing an edit.
                Comment.objects.select_for_update().get(pk=comment.pk)
            validate_comment(comment)
            comment.save()
            if attachment is not None:
                attachment.comment = comment
                try:
                    attachment.full_clean()
                except ValidationError as error:
                    raise ValidationError({"attachment": error.messages}) from error
                attachment.save()
    except Exception:
        # DB rollback does not roll back storage. Delete only the new file written
        # by this call, retaining the original exception if cleanup also fails.
        if attachment is not None and attachment.file._committed:
            try:
                attachment.file.delete(save=False)
            except Exception:
                logger.exception("Could not remove a failed comment upload")
        if was_adding:
            comment.pk = original_pk
            comment._state.adding = True
        comment._state.fields_cache.pop("attachment", None)
        raise
    return comment
