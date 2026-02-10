from fastapi import APIRouter, UploadFile
from app.services.graph_upload import GraphUploadClient
from app.core.config import settings

router = APIRouter(prefix="/attendant-images", tags=["AttendantImages"])

attendant_image_client = GraphUploadClient(settings.ATTENDANT_DOC_LIB)


@router.post("/{attendant_id}")
async def upload_attendant_image(attendant_id: int, file: UploadFile):
    content = await file.read()

    attendant_image_client.upload_file(
        file_name=file.filename,
        content=content,
        lookup_field_payload={
            "BranchAttendantDataIDLookupId": attendant_id
        },
    )

    return {"status": "attendant image uploaded"}
