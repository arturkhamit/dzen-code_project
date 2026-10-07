import json
from urllib.parse import urlencode
from urllib.request import urlopen

from django.conf import settings
from django.core.exceptions import ValidationError


def captcha_keys():
    site, secret = settings.RECAPTCHA_SITE_KEY, settings.RECAPTCHA_SECRET_KEY
    if not site or not secret:
        return "", ""
    return site, secret


def verify_captcha(token, hostname):
    _, secret = captcha_keys()
    if not secret or not 0 <= settings.RECAPTCHA_MIN_SCORE <= 1:
        raise ValidationError({"recaptcha": ["Verification is currently unavailable."]})
    if not token:
        raise ValidationError({"recaptcha": ["Verification is missing. Please try posting again."]})
    try:
        body = urlencode({"secret": secret, "response": token}).encode()
        with urlopen("https://www.google.com/recaptcha/api/siteverify", data=body, timeout=5) as response:
            result = json.loads(response.read(65536))
    except (OSError, ValueError):
        raise ValidationError({"recaptcha": ["Verification could not be reached. Please try again."]}) from None
    if not isinstance(result, dict) or result.get("success") is not True:
        raise ValidationError({"recaptcha": ["Verification failed. Please try posting again."]})
    if result.get("hostname") != hostname:
        raise ValidationError({"recaptcha": ["Verification failed for this site."]})
    # Match the action requested by frontend/src/lib/captcha.js, never POST data.
    if result.get("action") != "comment_create":
        raise ValidationError({"recaptcha": ["Verification failed for this action."]})
    score = result.get("score")
    if type(score) not in (int, float) or not settings.RECAPTCHA_MIN_SCORE <= score <= 1:
        raise ValidationError({"recaptcha": ["Verification failed. Please try again later."]})
