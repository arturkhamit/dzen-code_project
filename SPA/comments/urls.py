from django.urls import path

from comments.views.discussion import create_comment, discussion


app_name = "comments"
urlpatterns = [
    path("", discussion, name="list"),
    path("comments/create/", create_comment, name="create"),
]
