from pathlib import Path
from uuid import uuid4


def attachment_path(instance, filename):
    # Keep the submitted name for display only; storage paths are generated here.
    return f"comments/{uuid4().hex}{Path(filename).suffix.lower()}"
