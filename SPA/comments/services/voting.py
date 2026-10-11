from django.core.exceptions import ValidationError
from django.db import transaction

from accounts.services.tokens import AuthenticationError
from comments.models import Comment, CommentVote
from .notifications import notify_comments_changed


@transaction.atomic
def set_vote(comment_id, user, value):
    if user is None or not user.is_authenticated or not user.is_active:
        raise AuthenticationError("Sign in to vote.")
    if type(value) is not int or value not in (-1, 0, 1):
        raise ValidationError({"value": "Choose an upvote, downvote, or remove your vote."})
    # All voters lock the same comment first, preventing lost increments even
    # across workers. Explicit values also make retried requests idempotent.
    comment = Comment.objects.select_for_update().get(pk=comment_id)
    vote = CommentVote.objects.filter(comment=comment, user=user).first()
    previous = vote.value if vote else 0
    if value != previous:
        if value == 0:
            vote.delete()
        else:
            CommentVote.objects.update_or_create(comment=comment, user=user, defaults={"value": value})
        comment.vote_count += value - previous
        comment.save(update_fields=["vote_count"])
        notify_comments_changed()
    return comment
