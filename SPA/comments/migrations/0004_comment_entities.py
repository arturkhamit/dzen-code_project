from django.db import migrations, models

from comments.validators.entities import validate_plain_text


def convert_comments(apps, schema_editor):
    from comments.services.legacy_markup import convert_legacy_markup

    comments = apps.get_model("comments", "Comment").objects.using(schema_editor.connection.alias)
    for comment in comments.all().iterator(chunk_size=500):
        text, entities = convert_legacy_markup(comment.text)
        comments.filter(pk=comment.pk).update(text=text, entities=entities)


def restore_html(apps, schema_editor):
    from comments.serializers.markup import render_comment_text

    comments = apps.get_model("comments", "Comment").objects.using(schema_editor.connection.alias)
    for comment in comments.all().iterator(chunk_size=500):
        text = str(render_comment_text(comment.text, comment.entities))
        text = text.replace(' rel="nofollow ugc noopener noreferrer"', '')
        comments.filter(pk=comment.pk).update(text=text)


class Migration(migrations.Migration):
    dependencies = [("comments", "0003_comment_templates_and_attachments")]
    operations = [
        migrations.AddField("comment", "entities", models.JSONField(blank=True, default=list)),
        migrations.AlterField("comment", "text", models.TextField(max_length=10000, validators=[validate_plain_text])),
        migrations.RunPython(convert_comments, restore_html),
    ]
