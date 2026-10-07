from django.core.exceptions import ValidationError

from comments.models import Comment


def validate_comment(comment):
    # Built-in validation handles declared fields, uniqueness and DB constraints.
    # These additional rules depend on other rows and belong to the write service.
    comment.full_clean()
    errors = {}
    if not comment._state.adding:
        original = Comment.objects.filter(pk=comment.pk).values("parent_id").first()
        if original and original["parent_id"] != comment.parent_id:
            errors["parent"] = "An existing comment cannot be moved to another thread."
    ancestor_id = comment.parent_id
    seen = {comment.pk} if comment.pk else set()
    while ancestor_id is not None:
        if ancestor_id in seen:
            errors["parent"] = "A comment cannot reply to itself or a descendant."
            break
        seen.add(ancestor_id)
        ancestor_id = Comment.objects.filter(pk=ancestor_id).values_list("parent_id", flat=True).first()
    if errors:
        raise ValidationError(errors)
