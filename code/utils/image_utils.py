import base64
from pathlib import Path
from typing import Optional, Dict

MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".avif": "image/avif",
}


def load_image_as_base64(path: str) -> Optional[Dict[str, object]]:
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return None

    extension = file_path.suffix.lower()
    media_type = MEDIA_TYPES.get(extension)
    if media_type is None:
        return None

    with file_path.open("rb") as handle:
        raw = handle.read()
        encoded = base64.b64encode(raw).decode("utf-8")

    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": encoded,
        },
    }
