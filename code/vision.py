from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import struct

from PIL import Image, ImageFilter, ImageOps, ImageStat, UnidentifiedImageError

try:
    import imageio.v3 as iio
except Exception:
    try:
        import imageio as iio
    except Exception:
        iio = None


def _parse_webp_size(image_path: str) -> Optional[tuple[int, int]]:
    try:
        with open(image_path, "rb") as handle:
            header = handle.read(64)
    except OSError:
        return None

    if len(header) < 16 or header[0:4] != b"RIFF" or header[8:12] != b"WEBP":
        return None

    chunk_type = header[12:16]
    if chunk_type == b"VP8 ":
        if len(header) >= 30:
            width, height = struct.unpack_from("<HH", header, 26)
            return (width & 0x3fff, height & 0x3fff)
    elif chunk_type == b"VP8L":
        if len(header) >= 21:
            width = (header[20] | ((header[21] & 0x3F) << 8)) + 1
            height = (((header[21] & 0xC0) >> 6) | (header[22] << 2) | ((header[23] & 0x0F) << 10)) + 1
            return (width, height)
    elif chunk_type == b"VP8X":
        if len(header) >= 30:
            width = 1 + int.from_bytes(header[24:27], "little")
            height = 1 + int.from_bytes(header[27:30], "little")
            return (width, height)
    return None


@dataclass
class ImageMetadata:
    image_path: str
    image_id: str
    valid_image: bool
    width: int = 0
    height: int = 0
    quality_flags: List[str] = field(default_factory=list)
    caption: str = ""
    visible_object: str = "unknown"
    visible_part: str = "unknown"
    damage_keywords: List[str] = field(default_factory=list)
    detail_score: float = 0.0


def _load_image(image_path: str) -> Optional[Image.Image]:
    try:
        with Image.open(image_path) as image:
            return image.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError):
        pass

    if iio is None:
        return None

    try:
        array = iio.imread(image_path)
        if array is None:
            return None
        image = Image.fromarray(array)
        return image.convert("RGB")
    except Exception:
        return None


def load_image_metadata(image_path: str) -> ImageMetadata:
    metadata = ImageMetadata(
        image_path=image_path,
        image_id=Path(image_path).stem,
        valid_image=False,
    )
    image = _load_image(image_path)
    dimensions = None
    if image is None:
        dimensions = _parse_webp_size(image_path)
    if image is None and dimensions is None:
        metadata.caption = "Image could not be read or is not a supported image format."
        return metadata

    if image is not None:
        metadata.width, metadata.height = image.size
    else:
        metadata.width, metadata.height = dimensions

    metadata.valid_image = metadata.width > 0 and metadata.height > 0
    if metadata.width < 300 or metadata.height < 300:
        metadata.quality_flags.append("cropped_or_obstructed")
    if metadata.width * metadata.height < 180_000:
        metadata.quality_flags.append("low_light_or_glare")

    if image is not None:
        gray = ImageOps.grayscale(image)
        stat = ImageStat.Stat(gray)
        variance = float(stat.var[0]) if stat.var else 0.0
        brightness = float(stat.mean[0]) if stat.mean else 0.0
        if variance < 1200:
            metadata.quality_flags.append("blurry_image")
        if brightness < 30 or brightness > 230:
            if "low_light_or_glare" not in metadata.quality_flags:
                metadata.quality_flags.append("low_light_or_glare")

        edge_map = gray.filter(ImageFilter.FIND_EDGES)
        edge_stat = ImageStat.Stat(edge_map)
        edge_mean = float(edge_stat.mean[0]) if edge_stat.mean else 0.0
        metadata.detail_score = variance + edge_mean * 20.0

        if metadata.detail_score < 1000 and metadata.valid_image and "blurry_image" not in metadata.quality_flags:
            metadata.quality_flags.append("blurry_image")
    else:
        metadata.detail_score = 0.0

    metadata.caption = f"Image {metadata.image_id} with size {metadata.width}x{metadata.height}."
    return metadata


def analyze_images(image_paths: list[str]) -> list[ImageMetadata]:
    return [load_image_metadata(path) for path in image_paths]
