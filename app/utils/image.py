from fastapi import UploadFile, HTTPException
from PIL import Image
import io

# -------------------------------------------------
# Validate image (type & size)
# -------------------------------------------------
def validate_image(
    file: UploadFile,
    max_size_mb: int = 5,
    allowed_types=("image/jpeg", "image/png","image/jpg"),
):
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only JPG and PNG images are allowed",
        )

    file.file.seek(0, 2)  # move to end
    size = file.file.tell()
    file.file.seek(0)

    if size > max_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"Image size must be <= {max_size_mb}MB",
        )


# -------------------------------------------------
# Resize image (used before upload)
# -------------------------------------------------
def resize_image(
    file: UploadFile,
    max_width: int = 800,
    max_height: int = 800,
) -> bytes:
    """
    Resize image and return bytes ready for upload to SharePoint
    """
    image = Image.open(file.file)
    image.thumbnail((max_width, max_height))

    buffer = io.BytesIO()
    image.save(buffer, format=image.format or "JPEG")
    buffer.seek(0)

    return buffer.read()
