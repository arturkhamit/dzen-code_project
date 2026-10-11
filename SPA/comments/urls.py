from django.urls import path

from comments.views.discussion import create_comment, discussion
from comments.views.vote import vote


app_name = "comments"
urlpatterns = [
    path("", discussion, name="list"),
    path("comments/create/", create_comment, name="create"),
    path("comments/<int:comment_id>/vote/", vote, name="vote"),
]
