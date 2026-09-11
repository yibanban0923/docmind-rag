import hashlib
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from app.core.exceptions import InvalidUploadError

ALLOWED_MIME = {
    "pdf": {"application/pdf", "application/octet-stream"},
    "md": {"text/markdown", "text/plain", "application/octet-stream"},
}


@dataclass(slots=True)
class SavedUpload:
    path: Path
    filename: str
    file_type: str
    checksum: str
    size: int


def detect_file_type(filename: str | None) -> str:
    if not filename:
        raise InvalidUploadError("Filename is required")
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix == ".md":
        return "md"
    raise InvalidUploadError("Only .pdf and .md files are supported")


async def save_upload_to_temp(
    upload: UploadFile,
    *,
    temp_dir: Path,
    max_bytes: int,
) -> SavedUpload:
    file_type = detect_file_type(upload.filename)
    content_type = (upload.content_type or "application/octet-stream").lower()
    if content_type not in ALLOWED_MIME[file_type]:
        raise InvalidUploadError(f"Unexpected MIME type: {content_type}")

    temp_dir.mkdir(parents=True, exist_ok=True)
    suffix = ".pdf" if file_type == "pdf" else ".md"
    path = temp_dir / f"{uuid.uuid4().hex}{suffix}"
    sha = hashlib.sha256()
    size = 0

    try:
        with path.open("wb") as output:
            while True:
                block = await upload.read(1024 * 1024)
                if not block:
                    break
                size += len(block)
                if size > max_bytes:
                    raise InvalidUploadError("File exceeds maximum allowed size")
                sha.update(block)
                output.write(block)
        if size == 0:
            raise InvalidUploadError("Uploaded file is empty")
        return SavedUpload(
            path=path,
            filename=Path(upload.filename or "document").name,
            file_type=file_type,
            checksum=sha.hexdigest(),
            size=size,
        )
    except Exception:
        path.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()
