from io import BytesIO
from pathlib import Path
import warnings

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, ImageSequence

from comments.models import CommentAttachment
from comments.validators.attachment import IMAGE_ERRORS, IMAGE_FORMATS, read_attachment


IMAGE_SIZE = (320, 240)


def resize_image(data, image_format):
    """Re-encode the image in memory, preserving GIF frames and their duration."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as source:
                frames, durations = [], []
                sequence = ImageSequence.Iterator(source) if image_format == "GIF" else [source]
                for frame in sequence:
                    resized = ImageOps.exif_transpose(frame).convert("RGBA")
                    resized.thumbnail(IMAGE_SIZE, Image.Resampling.LANCZOS)
                    if image_format == "JPEG":
                        resized = resized.convert("RGB")
                    frames.append(resized)
                    durations.append(frame.info.get("duration", 100))
                output = BytesIO()
                options = {}
                if image_format == "GIF" and len(frames) > 1:
                    options = {"save_all": True, "append_images": frames[1:],
                               "duration": durations, "loop": source.info.get("loop", 0), "disposal": 2}
                # Even small images are re-encoded to remove metadata and trailing
                # payloads. Validation alone must never transform an upload.
                frames[0].info.clear()
                frames[0].save(output, format=image_format, **options)
                return output.getvalue(), frames[0].size
    except IMAGE_ERRORS as error:
        raise ValidationError("Upload a valid JPG, GIF or PNG image.") from error


def prepare_attachment(upload):
    """Return an unsaved attachment; this service writes neither files nor DB rows."""
    try:
        data, suffix = read_attachment(upload)
        name = Path(upload.name.replace("\\", "/")).name[:255]
        width = height = None
        kind = CommentAttachment.Kind.TEXT
        if suffix != ".txt":
            data, (width, height) = resize_image(data, IMAGE_FORMATS[suffix])
            kind = CommentAttachment.Kind.IMAGE
    except ValidationError as error:
        raise ValidationError({"attachment": error.messages}) from error
    return CommentAttachment(
        file=ContentFile(data, name=name), original_name=name, kind=kind,
        size=len(data), width=width, height=height,
    )
