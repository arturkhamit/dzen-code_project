from django.http import Http404, JsonResponse
from django.views.decorators.http import require_POST

from accounts.services.tokens import authenticated_user
from accounts.views.responses import api_errors
from comments.models import Comment
from comments.serializers.vote import deserialize_vote
from comments.services.voting import set_vote


@require_POST
@api_errors
def vote(request, comment_id):
    user = authenticated_user(request)
    value = deserialize_vote(request)
    try:
        if comment_id > 2**63 - 1:
            raise Comment.DoesNotExist
        comment = set_vote(comment_id, user, value)
    except Comment.DoesNotExist:
        raise Http404("Comment not found.") from None
    return JsonResponse({"comment_id": comment.pk, "vote_count": comment.vote_count, "user_vote": value})
