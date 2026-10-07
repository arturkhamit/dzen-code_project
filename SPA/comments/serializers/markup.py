from html import escape

from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

from comments.validators.markup import parse_comment_text


def render_comment_text(value):
    try:
        root = parse_comment_text(value)
    except ValidationError:
        # Older rows or bulk writes may bypass model validation. Escape them.
        return mark_safe(escape(str(value or "")))

    def render(node):
        content = escape(node.text or "")
        for child in node:
            attributes = "".join(f' {key}="{escape(val, quote=True)}"' for key, val in child.attrib.items())
            if child.tag == "a":
                attributes += ' rel="nofollow ugc noopener noreferrer"'
            content += f"<{child.tag}{attributes}>{render(child)}</{child.tag}>"
            content += escape(child.tail or "")
        return content

    # Only generated, allowlisted markup is marked safe, never the submitted text.
    return mark_safe(render(root))


def comment_plain_text(value):
    try:
        return "".join(parse_comment_text(value).itertext())
    except ValidationError:
        return str(value or "")
