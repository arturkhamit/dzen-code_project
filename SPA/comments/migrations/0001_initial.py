# Generated from comments models; review fields before applying in production.
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="CommentAuthor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("username", models.CharField(max_length=80, unique=True, validators=[django.core.validators.RegexValidator("^[A-Za-z0-9]+$", "Use Latin letters and digits only.")])),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("homepage", models.URLField(blank=True, max_length=2048)),
                ("avatar_url", models.URLField(blank=True, max_length=2048)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="CaptchaChallenge",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("answer_hash", models.CharField(max_length=128)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("consumed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"indexes": [models.Index(fields=["expires_at", "consumed_at"], name="comments_ca_expires_5253b9_idx")]},
        ),
        migrations.CreateModel(
            name="Comment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("username", models.CharField(db_index=True, max_length=80, validators=[django.core.validators.RegexValidator("^[A-Za-z0-9]+$", "Use Latin letters and digits only.")])),
                ("email", models.EmailField(db_index=True, max_length=254)),
                ("homepage", models.URLField(blank=True, max_length=2048)),
                ("avatar_url", models.URLField(blank=True, max_length=2048)),
                ("text", models.TextField()),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("vote_count", models.IntegerField(default=0)),
                ("parent", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="replies", to="comments.comment")),
                ("quoted_comment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="quoted_by", to="comments.comment")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="comments", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ("-created_at", "-id"),
                "indexes": [
                    models.Index(fields=["parent", "created_at"], name="comments_co_parent__10bc81_idx"),
                    models.Index(fields=["-created_at", "id"], name="comments_co_created_17a470_idx"),
                ],
            },
        ),
    ]
