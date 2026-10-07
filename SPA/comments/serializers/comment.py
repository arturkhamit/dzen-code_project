from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from .attachment import serialize_attachment
from .markup import comment_plain_text, render_comment_text


def display_url(value):
    # Imported or older data may bypass validation; never render an unsafe href.
    try:
        URLValidator(schemes=["http", "https"])(value)
    except ValidationError:
        return ""
    return value


def serialize_comment(comment, *, depth=0):
    """Build JSON data without adding presentation methods to models."""
    quoted = comment.quoted_comment
    return {
        "pk": comment.pk,
        "username": comment.username,
        "email": comment.email,
        "homepage": display_url(comment.homepage),
        "avatar_url": display_url(comment.avatar_url),
        "created_at": comment.created_at.isoformat(),
        "vote_count": comment.vote_count,
        "parent_id": comment.parent_id,
        "depth": depth,
        "rendered_text": render_comment_text(comment.text),
        "plain_text": comment_plain_text(comment.text),
        "quoted_comment": {
            "pk": quoted.pk, "username": quoted.username,
            "plain_text": comment_plain_text(quoted.text),
        } if quoted is not None else None,
        "attachment": serialize_attachment(getattr(comment, "attachment", None)),
    }


def serialize_comment_page(page):
    """Return a JSON-ready page; flat threads also support very deep replies."""
    roots = []
    for root in page.object_list:
        row = serialize_comment(root)
        row["thread"] = []
        pending = [(root, 0)]
        while pending:
            comment, depth = pending.pop()
            row["thread"].append(serialize_comment(comment, depth=depth))
            pending.extend((child, depth + 1) for child in reversed(page.replies_by_parent.get(comment.pk, [])))
        roots.append(row)
    return {
        "comments": roots, "page": page.number,
        "pages": page.paginator.num_pages, "count": page.paginator.count,
    }
