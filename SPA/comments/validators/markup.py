from xml.etree import ElementTree

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


MAX_TEXT_LENGTH = 10000
ALLOWED_TAGS = {"a": {"href", "title"}, "code": set(), "i": set(), "strong": set()}


def parse_comment_text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("Enter a comment.")
    if len(value) > MAX_TEXT_LENGTH:
        raise ValidationError(f"Use at most {MAX_TEXT_LENGTH} characters.")

    # XML enforces matching tags, quoted attributes and XHTML entities. Reject
    # declarations before parsing so a comment cannot define or expand entities.
    # Regex alone cannot validate nested markup. Write a literal '&' as '&amp;'.
    if "<!" in value or "<?" in value:
        raise ValidationError("Declarations, comments and processing instructions are not allowed.")
    try:
        root = ElementTree.fromstring(f"<comment>{value}</comment>")
    except (ElementTree.ParseError, ValueError) as error:
        raise ValidationError("Use valid XHTML with correctly closed tags and escaped & and < characters.") from error

    stack = [(child, False, 1) for child in root]
    while stack:
        node, inside_link, depth = stack.pop()
        if node.tag not in ALLOWED_TAGS or set(node.attrib) - ALLOWED_TAGS[node.tag]:
            raise ValidationError("Only a (href/title), code, i and strong tags are allowed.")
        if depth > 32:
            raise ValidationError("Formatting may be nested at most 32 levels deep.")
        if node.tag == "a":
            if inside_link:
                raise ValidationError("Links cannot contain other links.")
            href = node.get("href", "")
            if any(ord(char) < 32 or char.isspace() for char in href):
                raise ValidationError("Link addresses cannot contain whitespace or control characters.")
            URLValidator(schemes=["http", "https"])(href)
        stack.extend((child, inside_link or node.tag == "a", depth + 1) for child in node)
    if not "".join(root.itertext()).strip():
        raise ValidationError("Enter a comment containing text.")
    return root


def validate_comment_text(value):
    parse_comment_text(value)
