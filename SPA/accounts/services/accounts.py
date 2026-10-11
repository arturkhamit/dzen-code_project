from hashlib import sha256

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from accounts.models import Profile
from .identity import validate_available_email
from .tokens import AuthenticationError


class LoginThrottled(Exception):
    pass


def register_account(data):
    user = get_user_model()(username=data["username"], email=data["email"].strip())
    validate_available_email(user.email)
    if data["password1"] != data["password2"]:
        raise ValidationError({"password2": "The passwords do not match."})
    try:
        validate_password(data["password1"], user)
    except ValidationError as error:
        raise ValidationError({"password1": error.messages}) from error
    user.full_clean(exclude=["password"])
    user.set_password(data["password1"])
    try:
        with transaction.atomic():
            user.save()
            Profile.objects.create(user=user, homepage=data["homepage"])
    except IntegrityError:
        # Another request can claim an identity after validation. The database
        # enforces uniqueness; translate that race into the same form error.
        validate_available_email(user.email)
        if get_user_model().objects.filter(username=user.username).exists():
            raise ValidationError({"username": "This username is already taken."}) from None
        raise
    return user


def login_account(request, data):
    key = "login-attempts:" + sha256(data["username"].encode()).hexdigest()
    if cache.get(key, 0) >= settings.LOGIN_ATTEMPT_LIMIT:
        raise LoginThrottled
    user = authenticate(request, username=data["username"], password=data["password"])
    if user is None:
        cache.add(key, 0, timeout=settings.LOGIN_ATTEMPT_WINDOW)
        try:
            cache.incr(key)
        except ValueError:  # The counter may have expired between add and incr.
            cache.add(key, 1, timeout=settings.LOGIN_ATTEMPT_WINDOW)
        raise AuthenticationError("Incorrect username or password.")
    cache.delete(key)
    return user


def start_session(request, user):
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    request.session.set_expiry(settings.SESSION_COOKIE_AGE)


def update_profile(user, data):
    user.email = data["email"].strip()
    validate_available_email(user.email, user_id=user.pk)
    user.full_clean(exclude=["password"])
    try:
        with transaction.atomic():
            user.save(update_fields=["email"])
            profile, _ = Profile.objects.update_or_create(user=user, defaults={"homepage": data["homepage"]})
    except IntegrityError:
        validate_available_email(user.email, user_id=user.pk)
        raise
    # Replace a possibly cached reverse relation before serializing the result.
    user.profile = profile
    return user


def change_password(request, user, data):
    # Resolve the current session before changing the password invalidates it.
    keep_session = request.user.is_authenticated and request.user.pk == user.pk
    form = PasswordChangeForm(user, data)
    if not form.is_valid():
        raise ValidationError(form.errors.as_data())
    form.save(commit=False).save(update_fields=["password"])
    if keep_session:
        update_session_auth_hash(request, user)
    return user
