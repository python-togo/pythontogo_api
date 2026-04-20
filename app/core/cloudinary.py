import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile

from app.core.settings import settings

cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True,
)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/svg+xml"}
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def _subfolder(sub: str) -> str:
    return f"{settings.cloudinary_folder}/{sub}"


async def upload_image(file: UploadFile, subfolder: str, public_id: str | None = None) -> str:
    """Upload an image to Cloudinary and return the secure URL."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: JPEG, PNG, WEBP, SVG",
        )

    contents = await file.read()
    if len(contents) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds the 5 MB size limit")

    options: dict = {
        "folder": _subfolder(subfolder),
        "overwrite": True,
        "resource_type": "image",
    }
    if public_id:
        options["public_id"] = public_id

    result = cloudinary.uploader.upload(contents, **options)
    return result["secure_url"]


async def delete_image(public_id: str) -> None:
    """Delete an image from Cloudinary by its public_id."""
    cloudinary.uploader.destroy(public_id, resource_type="image")
