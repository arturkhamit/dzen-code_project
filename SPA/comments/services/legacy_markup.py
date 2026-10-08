"""Convert old XHTML rows for migration 0004; retain this import path."""

from django.core.exceptions import ValidationError

from comments.validators.markup import parse_comment_text


def convert_legacy_markup(value):
    try:
        root = parse_comment_text(value)
    except ValidationError:
        return value, []
    parts, entities, offset = [], [], 0
    kinds = {"strong": "bold", "i": "italic", "code": "code", "a": "text_link"}

    def append(text, marks):
        nonlocal offset
        text = text or ""
        length = len(text.rstrip().encode("utf-16-le")) // 2
        # Old nested formatting inside code becomes literal code formatting.
        marks = [{"type": "code"}] if any(mark["type"] == "code" for mark in marks) else marks
        if length:
            entities.extend(mark | {"offset": offset, "length": length} for mark in marks)
        parts.append(text)
        offset += len(text.encode("utf-16-le")) // 2

    def walk(node, marks):
        append(node.text, marks)
        for child in node:
            mark = {"type": kinds[child.tag]}
            if child.tag == "a":
                mark |= {"url": child.get("href"), "title": child.get("title", "")}
            walk(child, marks + [mark])
            append(child.tail, marks)

    walk(root, [])
    return "".join(parts), entities
