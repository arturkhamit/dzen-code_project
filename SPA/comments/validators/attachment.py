from io import BytesIO
from pathlib import Path
import warnings

from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError


MAX_TEXT_BYTES = 100 * 1024
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
IMAGE_FORMATS = {".jpg": "JPEG", ".jpeg": "JPEG", ".gif": "GIF", ".png": "PNG"}
IMAGE_ERRORS = (
    UnidentifiedImageError, OSError, ValueError, SyntaxError,
    Image.DecompressionBombError, Image.DecompressionBombWarning,
)


def validate_text_file(data):
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValidationError("Save the TXT file using UTF-8 encoding.") from error
    if any(ord(char) < 32 and char not in "\t\n\r" for char in text):
        raise ValidationError("TXT attachments cannot contain binary data.")


def validate_image_file(data, suffix):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as source:
                if source.format != IMAGE_FORMATS[suffix]:
                    raise ValidationError("The image contents do not match its extension.")
                frames = getattr(source, "n_frames", 1)
                if frames > 200 or source.width * source.height * frames > MAX_IMAGE_PIXELS:
                    raise ValidationError("The image is too complex to process.")
                source.verify()
    except IMAGE_ERRORS as error:
        raise ValidationError("Upload a valid JPG, GIF or PNG image.") from error


def read_attachment(upload):
    """Read bounded, validated bytes without changing the caller's stream position."""
    suffix = Path(upload.name).suffix.lower()
    if suffix not in IMAGE_FORMATS and suffix != ".txt":
        raise ValidationError("Choose a JPG, GIF, PNG or TXT file.")
    limit = MAX_TEXT_BYTES if suffix == ".txt" else MAX_IMAGE_BYTES
    position = upload.tell()
    try:
        upload.seek(0)
        data = upload.read(limit + 1)

        if data and len(data) > limit:
            raise ValidationError("TXT files must be at most 100 KB." if suffix == ".txt"
                                  else "Images must be at most 10 MB.")
    finally:
        upload.seek(position)
    if not data:
        raise ValidationError("The attachment is empty.")

    if suffix == ".txt":
        validate_text_file(data)
    else:
        validate_image_file(data, suffix)
    return data, suffix
