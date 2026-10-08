from html import escape

from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

from comments.validators.entities import utf16_boundaries, validate_entities


def render_comment_text(value, entities=None):
    try:
        entities = validate_entities(value, [] if entities is None else entities)
    except ValidationError:
        # Older rows or bulk writes may bypass model validation. Escape them.
        return mark_safe(escape(str(value or "")))

    positions, output, stack, cursor = utf16_boundaries(value), [], [], 0
    tags = {"bold": "strong", "italic": "i", "code": "code", "text_link": "a"}
    for entity in entities:
        start, end = positions[entity["offset"]], positions[entity["offset"] + entity["length"]]
        while stack and stack[-1][0] <= start:
            stop, tag = stack.pop()
            output.append(escape(value[cursor:stop]) + f"</{tag}>")
            cursor = stop
        tag, attributes = tags[entity["type"]], ""
        if tag == "a":
            attributes = f' href="{escape(entity["url"], quote=True)}"'
            if "title" in entity:
                attributes += f' title="{escape(entity["title"], quote=True)}"'
            attributes += ' rel="nofollow ugc noopener noreferrer"'
        output.append(escape(value[cursor:start]) + f"<{tag}{attributes}>")
        cursor = start
        stack.append((end, tag))
    while stack:
        end, tag = stack.pop()
        output.append(escape(value[cursor:end]) + f"</{tag}>")
        cursor = end
    output.append(escape(value[cursor:]))
    # Only generated markup is marked safe; the message itself is always escaped.
    return mark_safe("".join(output))


def comment_plain_text(value):
    return str(value or "")
