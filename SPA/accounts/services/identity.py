from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.functions import Lower, Trim


def accounts_with_email(email):
    # Match the database's unique index, including older mixed-case addresses.
    return get_user_model().objects.alias(email_key=Lower(Trim("email"))).filter(
        email_key=email.strip().lower(),
    )


def validate_available_email(email, *, user_id=None):
    if accounts_with_email(email).exclude(pk=user_id).exists():
        raise ValidationError({"email": "An account with this email already exists."})
