from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


MAX_TEXT_LENGTH = 10000
ENTITY_TYPES = {"bold", "italic", "code", "text_link"}


def utf16_boundaries(text):
    # Telegram offsets count UTF-16 units; Python indexes Unicode code points.
    positions, offset = {0: 0}, 0
    for index, char in enumerate(text, 1):
        offset += 2 if ord(char) > 0xFFFF else 1
        positions[offset] = index
    return positions


def validate_plain_text(text):
    if not isinstance(text, str) or not text.strip():
        raise ValidationError("Enter a comment.")
    try:
        length = len(text.encode("utf-16-le")) // 2
    except UnicodeEncodeError:
        raise ValidationError("Enter valid Unicode text.") from None
    if "\0" in text or length > MAX_TEXT_LENGTH:
        raise ValidationError(f"Use at most {MAX_TEXT_LENGTH} characters and no null characters.")


def validate_entities(text, entities):
    """Validate and normalize formatting without interpreting text as HTML."""
    validate_plain_text(text)
    if not isinstance(entities, list) or len(entities) > 1000:
        raise ValidationError("Use a list of at most 1,000 formatting entities.")
    positions, cleaned = utf16_boundaries(text), []
    for entity in entities:
        if not isinstance(entity, dict) or not isinstance(entity.get("type"), str) or entity["type"] not in ENTITY_TYPES:
            raise ValidationError("Only bold, italic, code and text_link formatting is supported.")
        kind, start, length = entity["type"], entity.get("offset"), entity.get("length")
        allowed = {"type", "offset", "length"} | ({"url", "title"} if kind == "text_link" else set())
        if set(entity) - allowed or type(start) is not int or type(length) is not int:
            raise ValidationError("Formatting requires integer offsets and lengths, with no extra attributes.")
        end = start + length
        if length <= 0 or start not in positions or end not in positions:
            raise ValidationError("Formatting must stay within the text and cannot split an emoji.")
        if kind == "text_link":
            url, title = entity.get("url"), entity.get("title", "")
            if not isinstance(url, str) or any(char.isspace() or ord(char) < 32 for char in url):
                raise ValidationError("Use a complete HTTP or HTTPS link without spaces.")
            URLValidator(schemes=["http", "https"])(url)
            if not isinstance(title, str) or len(title) > MAX_TEXT_LENGTH:
                raise ValidationError("Enter a valid link title.")
            try:
                (url + title).encode("utf-8")
            except UnicodeEncodeError:
                raise ValidationError("Enter valid Unicode in the link.") from None
            if "\0" in title:
                raise ValidationError("Link titles cannot contain null characters.")
        # Trailing spaces remain in the text but are not part of the entity.
        content = text[positions[start]:positions[end]].rstrip()
        if content:
            cleaned.append(entity | {"length": len(content.encode("utf-16-le")) // 2})
    cleaned.sort(key=lambda entity: (entity["offset"], -entity["length"], entity["type"]))
    stack = []
    for entity in cleaned:
        start, end = entity["offset"], entity["offset"] + entity["length"]
        while stack and stack[-1]["offset"] + stack[-1]["length"] <= start:
            stack.pop()
        if stack and end > stack[-1]["offset"] + stack[-1]["length"]:
            raise ValidationError("Formatting ranges must be separate or fully nested.")
        if stack and (entity["type"] == "code" or any(parent["type"] == "code" for parent in stack)):
            raise ValidationError("Code cannot overlap other formatting.")
        if entity["type"] == "text_link" and any(parent["type"] == "text_link" for parent in stack):
            raise ValidationError("Links cannot contain other links.")
        if len(stack) >= 32:
            raise ValidationError("Formatting may be nested at most 32 levels deep.")
        stack.append(entity)
    return cleaned
