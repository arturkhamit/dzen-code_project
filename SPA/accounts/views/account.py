from django.conf import settings
from django.contrib.auth import logout as end_session
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.http import require_http_methods, require_POST

from accounts.serializers.account import (
    LoginInput, PasswordInput, ProfileInput, RegistrationInput, deserialize_account, serialize_user,
)
from accounts.services.accounts import change_password, login_account, register_account, start_session, update_profile
from accounts.services.tokens import AuthenticationError, authenticated_user, issue_access_token
from .responses import api_errors


def login_response(request, user, *, status=200):
    return JsonResponse({
        "user": serialize_user(user), "access_token": issue_access_token(user),
        "expires_in": settings.JWT_ACCESS_SECONDS, "csrf_token": get_token(request),
    }, status=status)


@api_errors
@require_POST
def register(request):
    user = register_account(deserialize_account(request, RegistrationInput))
    start_session(request, user)
    return login_response(request, user, status=201)


@api_errors
@require_POST
def login(request):
    user = login_account(request, deserialize_account(request, LoginInput))
    start_session(request, user)
    return login_response(request, user)


@api_errors
@require_POST
def refresh(request):
    if not request.user.is_authenticated:
        raise AuthenticationError("Please sign in.")
    return login_response(request, request.user)


@api_errors
@require_POST
def logout(request):
    end_session(request)
    return HttpResponse(status=204)


@api_errors
@require_http_methods(["GET", "PATCH"])
def me(request):
    user = authenticated_user(request)
    if request.method == "PATCH":
        data = deserialize_account(request, ProfileInput, defaults=serialize_user(user))
        update_profile(user, data)
    return JsonResponse({"user": serialize_user(user)})


@api_errors
@require_POST
def password(request):
    user = authenticated_user(request)
    change_password(request, user, deserialize_account(request, PasswordInput))
    return login_response(request, user)
