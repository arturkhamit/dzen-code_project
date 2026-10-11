from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from accounts.services.identity import accounts_with_email


def validate_guest_identity(comment):
    # Registered identities are reserved. Previous guest posts do not reserve
    # details, otherwise a guest could never post a second comment.
    errors = {}
    if get_user_model().objects.filter(username__iexact=comment.username.strip()).exists():
        errors["username"] = "This username belongs to an account. Sign in or use another name."
    if accounts_with_email(comment.email).exists():
        errors["email"] = "This email belongs to an account. Sign in or use another email."
    if errors:
        raise ValidationError(errors)


def set_comment_identity(comment, user):
    """Keep a snapshot of the authenticated account, ignoring posted identities."""
    if user is not None:
        profile = getattr(user, "profile", None)
        comment.user = user
        comment.username = user.username
        comment.email = user.email
        comment.homepage = profile.homepage if profile else ""
