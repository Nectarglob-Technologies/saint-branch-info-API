from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.face_service import FaceService

router = APIRouter(prefix="/face", tags=["Face"])
face_service = FaceService()

@router.post("/register/saint/{saint_id}")
async def register_face(saint_id: int, file: UploadFile = File(...)):
    image_bytes = await file.read()
    face_service.register_saint_face(saint_id, image_bytes)
    return {"status": "registered"}

@router.post("/verify")
async def verify_face(file: UploadFile = File(...)):
    image_bytes = await file.read()
    return face_service.verify_face(image_bytes)

from fastapi import APIRouter, UploadFile, File, Query
from app.services.face_service import FaceService

router = APIRouter(prefix="/face", tags=["Face Search"])

face_service = FaceService()


@router.post("/search-by-image")
async def search_by_image(
    file: UploadFile = File(...),
    mode: str = Query("default", enum=["default", "review"]),
):
    try:

        image_bytes = await file.read()

        result = face_service.verify_face_with_policy(
            image_bytes=image_bytes,
            mode=mode,
        )

        return result

    # 🔹 CLIENT ERRORS (send exact message to UI)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    # 🔹 EVERYTHING ELSE = REAL SERVER ERROR
    except Exception as e:
        print("SEARCH BY IMAGE ERROR:", repr(e))
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )