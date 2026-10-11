import json

from django.core.exceptions import ValidationError


def deserialize_vote(request):
    try:
        if request.content_type != "application/json" or len(request.body) > 1024:
            raise ValueError
        data = json.loads(request.body)
        if not isinstance(data, dict) or type(data.get("value")) is not int or data["value"] not in (-1, 0, 1):
            raise ValueError
    except (ValueError, UnicodeDecodeError, RecursionError):
        raise ValidationError({"value": "Choose 1 (upvote), -1 (downvote), or 0 (remove vote)."}) from None
    return data["value"]
