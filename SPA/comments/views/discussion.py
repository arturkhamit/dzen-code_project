from urllib.parse import urlencode, urlsplit

from django.core.exceptions import ValidationError
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.vary import vary_on_headers
from django.conf import settings

from accounts.services.tokens import authenticated_user
from accounts.views.responses import api_errors
from comments.models import Comment
from comments.serializers.comment import serialize_comment_page
from comments.serializers.submission import deserialize_comment, reference_id, serialize_errors
from comments.services.captcha import captcha_keys, verify_captcha
from comments.services.comment_identity import set_comment_identity
from comments.services.list_comments import SORT_FIELDS, comment_page_number, get_comment_page
from comments.services.save_comment import save_comment


def selected_sort(value):
    return value if value in SORT_FIELDS else "newest"


@require_GET
@api_errors
@vary_on_headers("Accept", "Authorization")
def discussion(request):
    # The page is public; a supplied JWT adds only this visitor's vote state.
    user = authenticated_user(request) if "Authorization" in request.headers else None
    sort = selected_sort(request.GET.get("sort"))
    number = request.GET.get("page", 1)
    if "comment" in request.GET:
        try:
            number = comment_page_number(reference_id(request.GET["comment"]), sort)
        except (ValidationError, Comment.DoesNotExist):
            raise Http404("Comment not found.") from None
    data = serialize_comment_page(get_comment_page(number, sort, user=user))
    if request.get_preferred_type(["text/html", "application/json"]) == "application/json":
        return JsonResponse(data)
    return render(request, "comments/comment_list.html", {
        "page_data": data, "sort": sort,
        "list_url": reverse("comments:list"), "form_action": reverse("comments:create"),
        "recaptcha_site_key": captcha_keys()[0],
        "captcha_required": not settings.DEBUG,
        "auth_urls": {name: reverse(f"accounts:{name}") for name in (
            "register", "login", "refresh", "logout", "me", "password",
        )},
    })


@require_POST
@api_errors
def create_comment(request):
    try:
        # Reject expired tokens before consuming CAPTCHA or writing any files.
        user = authenticated_user(request, optional=True)
        comment = deserialize_comment(request.POST, request.FILES)
        set_comment_identity(comment, user)
        if not settings.DEBUG:
            verify_captcha(
                request.POST.get("g-recaptcha-response"),
                urlsplit("//" + request.get_host()).hostname,
            )
        # Validation and the write transaction stay in the existing service.
        save_comment(comment, upload=request.FILES.get("attachment"))
    except ValidationError as error:
        return JsonResponse(serialize_errors(error), status=400)
    sort = selected_sort(request.POST.get("sort"))
    number = comment_page_number(comment.pk, sort)
    return JsonResponse({
        "comment_id": comment.pk,
        "list_url": reverse("comments:list") + "?" + urlencode({"page": number, "sort": sort}),
    }, status=201)
