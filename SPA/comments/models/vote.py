from django.conf import settings
from django.db import models


class CommentVote(models.Model):
    comment = models.ForeignKey("comments.Comment", on_delete=models.CASCADE, related_name="votes")
    # Keep historical votes and their score if an account is deleted, just as
    # comments keep the author's snapshot after account deletion.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    value = models.SmallIntegerField(choices=[(1, "Upvote"), (-1, "Downvote")])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["comment", "user"], name="comments_one_vote_per_user"),
            models.CheckConstraint(condition=models.Q(value__in=[-1, 1]), name="comments_vote_direction"),
        ]
