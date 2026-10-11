import time

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.crypto import constant_time_compare


class AuthenticationError(Exception):
    pass


def issue_access_token(user):
    now = int(time.time())
    return jwt.encode({
        "sub": str(user.pk), "iat": now, "exp": now + settings.JWT_ACCESS_SECONDS,
        "iss": settings.JWT_ISSUER, "aud": settings.JWT_AUDIENCE, "type": "access",
        # This HMAC changes with the password; it is not the stored password hash.
        "auth_hash": user.get_session_auth_hash(),
    }, settings.SECRET_KEY, algorithm="HS256")


def authenticated_user(request, *, optional=False):
    header = request.headers.get("Authorization")
    if header is None:
        # A session-only request must renew its JWT, never impersonate a guest.
        if optional and not request.user.is_authenticated:
            return None
        raise AuthenticationError("Please sign in or renew your login.")
    user_model = get_user_model()
    try:
        scheme, token = header.split()
        if scheme.lower() != "bearer":
            raise ValueError
        claims = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"],
            issuer=settings.JWT_ISSUER, audience=settings.JWT_AUDIENCE,
            options={"require": ["sub", "iat", "exp", "iss", "aud", "type", "auth_hash"]},
        )
        if claims["type"] != "access" or not isinstance(claims["auth_hash"], str):
            raise ValueError
        if not claims["sub"].isascii() or not claims["sub"].isdecimal() or len(claims["sub"]) > 19:
            raise ValueError
        user_id = int(claims["sub"])
        if not 0 < user_id <= 2**63 - 1:
            raise ValueError
        user = user_model.objects.select_related("profile").get(pk=user_id, is_active=True)
        if not constant_time_compare(claims["auth_hash"], user.get_session_auth_hash()):
            raise ValueError
        return user
    except (jwt.InvalidTokenError, ValueError, TypeError, OverflowError, user_model.DoesNotExist):
        raise AuthenticationError("Your login has expired. Please sign in again.") from None
