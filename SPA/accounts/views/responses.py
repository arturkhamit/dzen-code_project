from functools import wraps

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from redis.exceptions import RedisError

from accounts.services.accounts import LoginThrottled
from accounts.services.tokens import AuthenticationError


def api_errors(view):
    @never_cache
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except ValidationError as error:
            return JsonResponse({"errors": getattr(error, "message_dict", {"__all__": error.messages})}, status=400)
        except AuthenticationError as error:
            response = JsonResponse({"errors": {"__all__": [str(error)]}}, status=401)
            response["WWW-Authenticate"] = "Bearer"
            return response
        except LoginThrottled:
            response = JsonResponse({"errors": {"__all__": ["Too many login attempts. Try again in five minutes."]}}, status=429)
            response["Retry-After"] = str(settings.LOGIN_ATTEMPT_WINDOW)
            return response
        except RedisError:
            return JsonResponse({"errors": {"__all__": ["Login is temporarily unavailable. Please try again."]}}, status=503)
    return wrapped
