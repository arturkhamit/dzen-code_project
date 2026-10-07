from django.core.exceptions import ValidationError

from comments.models import Comment


def reference_id(value):
    if not value:
        return None
    if not value.isascii() or not value.isdecimal() or len(value) > 19:
        raise ValidationError("Choose a valid comment reference.")
    number = int(value)
    if not 0 < number <= 2**63 - 1:
        raise ValidationError("Choose a valid comment reference.")
    return number


def deserialize_comment(data, files):
    """Read the public input fields; model validation belongs to save_comment."""
    if len(files.getlist("attachment")) > 1:
        raise ValidationError({"attachment": ["Attach only one file."]})
    return Comment(
        **{field: data.get(field, "") for field in ("username", "email", "homepage", "text")},
        parent_id=reference_id(data.get("parent_id")),
        quoted_comment_id=reference_id(data.get("quoted_comment_id")),
    )


def serialize_errors(error):
    fields = {"username", "email", "homepage", "text", "attachment", "recaptcha"}
    result = {}
    for field, messages in getattr(error, "message_dict", {"__all__": error.messages}).items():
        result.setdefault(field if field in fields else "__all__", []).extend(messages)
    return {"errors": result}
