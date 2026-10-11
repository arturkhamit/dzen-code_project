from django.conf import settings
from django.db import migrations, models
from django.db.models.functions import Lower, Trim


EMAIL_UNIQUE = models.UniqueConstraint(
    Lower(Trim("email")), condition=~models.Q(email=""),
    name="accounts_user_email_unique",
)


def add_email_unique(apps, schema_editor):
    user = apps.get_model(settings.AUTH_USER_MODEL)
    duplicates = (
        user.objects.using(schema_editor.connection.alias).exclude(email="")
        .annotate(email_key=Lower(Trim("email"))).values("email_key")
        .annotate(total=models.Count("pk")).filter(total__gt=1)
    )
    if duplicates.exists():
        # Do not delete or merge existing accounts automatically.
        raise RuntimeError(
            "Duplicate account emails exist (ignoring case/spaces). Give those "
            "accounts distinct emails in Django admin, then run migrate again."
        )
    schema_editor.add_constraint(user, EMAIL_UNIQUE)


def remove_email_unique(apps, schema_editor):
    schema_editor.remove_constraint(apps.get_model(settings.AUTH_USER_MODEL), EMAIL_UNIQUE)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]
    # Django owns auth.User's model state. Add an index to its existing table
    # without replacing User or modifying Django's installed migrations.
    # Blank emails remain allowed for older/admin accounts.
    operations = [migrations.RunPython(add_email_unique, remove_email_unique)]
