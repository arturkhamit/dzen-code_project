import json

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


# Django's fields already handle email/URL validation; no REST framework needed.
class ProfileInput(forms.Form):
    email = forms.EmailField(max_length=254)
    homepage = forms.URLField(
        required=False, max_length=2048, validators=[URLValidator(schemes=["http", "https"])],
    )


class RegistrationInput(ProfileInput):
    username = forms.RegexField(
        r"\A[A-Za-z0-9_-]+\Z", max_length=80,
        error_messages={"invalid": "Use Latin letters (A–Z, a–z), digits (0–9), underscores (_) or dashes (-), with no spaces. Example: Alex_123-test."},
    )
    password1 = forms.CharField(strip=False, max_length=128)
    password2 = forms.CharField(strip=False, max_length=128)


class LoginInput(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(strip=False, max_length=128)


class PasswordInput(forms.Form):
    old_password = forms.CharField(strip=False, max_length=128)
    new_password1 = forms.CharField(strip=False, max_length=128)
    new_password2 = forms.CharField(strip=False, max_length=128)


def deserialize_account(request, input_class, *, defaults=None):
    try:
        if request.content_type != "application/json" or len(request.body) > 16384:
            raise ValueError
        data = json.loads(request.body)
        if not isinstance(data, dict):
            raise ValueError
        if any(name in data and not isinstance(data[name], str) for name in input_class.base_fields):
            raise ValueError
    except (ValueError, UnicodeDecodeError, RecursionError):
        raise ValidationError("Send a JSON object containing text fields.") from None
    form = input_class(data=(defaults or {}) | data)
    if not form.is_valid():
        raise ValidationError(form.errors.as_data())
    return form.cleaned_data


def serialize_user(user):
    profile = getattr(user, "profile", None)
    return {
        "id": user.pk, "username": user.username, "email": user.email,
        "homepage": profile.homepage if profile else "",
    }
