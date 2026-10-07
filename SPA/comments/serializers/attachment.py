def serialize_attachment(attachment):
    if attachment is None or not attachment.file:
        return None
    return {
        "file": {"url": attachment.file.url},
        "original_name": attachment.original_name,
        "kind": attachment.kind,
        "size": attachment.size,
        "width": attachment.width,
        "height": attachment.height,
    }
