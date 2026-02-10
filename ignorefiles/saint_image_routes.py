from fastapi import APIRouter, UploadFile
from app.services.graph_upload import GraphUploadClient
from app.core.config import settings

router = APIRouter(prefix="/saint-images", tags=["SaintImages"])

saint_image_client = GraphUploadClient(settings.SAINT_DOC_LIB)


@router.post("/{saint_id}")
async def upload_saint_image(saint_id: int, file: UploadFile):
    content = await file.read()

    saint_image_client.upload_file(
        file_name=file.filename,
        content=content,
        lookup_field_payload={
            "BranchSaintsDataIDLookupId": saint_id
        },
    )

    return {"status": "saint image uploaded"}
