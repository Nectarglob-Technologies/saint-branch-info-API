from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends
import uuid
from typing import Optional
from fastapi import Query
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from app.services.attendant_service import GraphSaintAttendantClient





# from fastapi import (
#     APIRouter,
#     UploadFile,
#     File,
#     BackgroundTasks,
# )


from app.services.attendant_service import GraphSaintAttendantClient
from app.schemas.attendant_item import (
    BranchAttendantCreate,
    BranchAttendantUpdate,
    BranchAttendantResponse,
)
from app.utils.image import validate_image

router = APIRouter(
    prefix="/saint-attendants",
    tags=["SaintAttendants"]
)

client = GraphSaintAttendantClient()



# ------------------------------------------------------------------
# CREATE attendant (no image)
# ------------------------------------------------------------------
@router.post("/", response_model=BranchAttendantResponse)
# def BranchAttendantCreate(payload: BranchAttendantCreate):
def create_attendant(payload: BranchAttendantCreate):
    item = client.create_attendant(payload.model_dump())
    return {
        "success": True,
        "sharepoint_response": {
            "id": item.id,
            **item.fields
        }
    }

# ------------------------------------------------------------------
# CREATE attendant (with image)
# ------------------------------------------------------------------
from fastapi import Depends

@router.post("/with-image", response_model=BranchAttendantResponse)
def create_saint_attendant_with_image(
    payload: BranchAttendantCreate = Depends(BranchAttendantCreate.as_form),
    photo: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    validate_image(photo)

    # 1️⃣ Generate UUID for attendant
    attendant_uuid = str(uuid.uuid4())

    # 2️ Prepare payload for SharePoint
    data = payload.model_dump()
    data.update({
        #"AttendantUUID": attendant_uuid,
        "IsActive": True
    })
    
    # 3️⃣ Create attendant list item
    item = client.create_attendant(data)
    attendant_id = item.id

    # 4️⃣ Background task: image upload + face registration
    background_tasks.add_task(
        client.upload_attendant_photo_background,
        attendant_id=attendant_id,
        file=photo,
    )

    # 5️⃣ Background task: QR image/PDF generation + upload
    #background_tasks.add_task(
    #    client.upload_attendant_qr_pdf_background,
    #    attendant_id=attendant_id,
    #    item=item,
    #)

    # 6️⃣ Fetch latest item data
    item = client.get_attendant_item_by_id(attendant_id)

    # 7️⃣ Return response
    return {
        "success": True,
        "sharepoint_response": {
            "id": attendant_id,
            "AttendantUUID": attendant_uuid,
            **item["fields"],
        },
    }


# from fastapi import Depends

# @router.post("/with-image", response_model=BranchAttendantResponse)
# def create_saint_attendant_with_image(
#     payload: BranchAttendantCreate = Depends(BranchAttendantCreate.as_form),
#     photo: UploadFile = File(...),
#     background_tasks: BackgroundTasks = BackgroundTasks(),
# ):

#     validate_image(photo)

#     item = client.create_attendant(payload.model_dump())

#     background_tasks.add_task(
#         client.upload_attendant_image_background,
#         attendant_id=item.id,
#         file=photo
#     )

#     return {
#         "success": True,
#         "sharepoint_response": {
#             "id": item.id,
#             **item.fields
#         }
#     }


# @router.post("/with-image", response_model=BranchAttendantResponse)
# def create_saint_attendant_with_image(
#     payload: BranchAttendantCreate,
#     background_tasks: BackgroundTasks,
#     photo: UploadFile = File(...)
# ):
#     validate_image(photo)

#     item = client.create_attendant(payload.model_dump())

#     background_tasks.add_task(
#         client.upload_attendant_image_background,
#         attendant_id=item.id,
#         file=photo
#     )

#     return {
#         "success": True,
#         "sharepoint_response": {
#             "id": item.id,
#             **item.fields
#         }
#     }

# ------------------------------------------------------------------
# LIST attendants
# ------------------------------------------------------------------
@router.get("/", response_model=list[BranchAttendantResponse])
def list_saint_attendants():
    items = client.get_attendants()
    return [
        {
            "success": True,
            "sharepoint_response": {
                "id": i.id,
                **i.fields
            }
        }
        for i in items
    ]
from app.schemas.saint_item import BranchSaintMultiRecordsResponse

@router.get("/search/paginated", response_model=BranchSaintMultiRecordsResponse)
def search_attendants_paginated(
    AttendantName: Optional[str] = Query(None),
    AttendantContactNo: Optional[str] = Query(None),
    page_size: int = Query(20, le=100),
    cursor: Optional[str] = Query(None),
):
    filters = {}

    # 🔵 Filter by Name (Title column in SharePoint)
    if AttendantName:
        filters["Title"] = AttendantName

    # 🔵 Filter by Contact
    if AttendantContactNo:
        filters["AttendantContactNo"] = AttendantContactNo

    result = client.get_attendants_paginated(
        filters=filters or None,
        page_size=page_size,
        next_link=cursor,
    )

    items = result["items"]

    response_items = [
        {
            "id": item.id,
            **item.fields
        }
        for item in items
    ]

    return {
        "success": True,
        "count": len(response_items),
        "next_cursor": result["next_cursor"],
        "sharepoint_response": response_items,
    }


# Attendant Photo GET Logic
@router.get("/{attendant_id}/photo")
def get_attendant_photo(attendant_id: int, filename: str):
    try:
        stream = client.download_attendant_file_stream(
            attendant_id=attendant_id,
            filename=filename
        )

        return StreamingResponse(
            stream,
            media_type="image/jpeg",
            headers={"Content-Disposition": "inline"}
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ------------------------------------------------------------------
# UPDATE attendant
# ------------------------------------------------------------------
@router.put("/{item_id}")
def update_saint_attendant(
    item_id: int,
    payload: BranchAttendantUpdate
):
    client.update_attendant(
        item_id,
        payload.model_dump(exclude_none=True)
    )
    return {"status": "updated"}

# ------------------------------------------------------------------
# DELETE attendant
# ------------------------------------------------------------------
@router.delete("/{item_id}")
def delete_saint_attendant(item_id: int):
    client.delete_attendant(item_id)
    return {"status": "deleted"}
