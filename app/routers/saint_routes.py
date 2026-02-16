from fastapi import (
    APIRouter,
    UploadFile,
    File,
    BackgroundTasks,
    Form,
    HTTPException,
    Depends
)
import json
from typing import Optional
from fastapi import Query

from app.services.saint_service import GraphBranchSaintClient
from app.schemas.saint_item import (
    BranchSaintCreate,
    BranchSaintUpdate,
    BranchSaintSingleRecordResponse,
    BranchSaintMultiRecordsResponse
)
from app.utils.image import validate_image

from fastapi import Request

router = APIRouter(prefix="/branch-saints", tags=["BranchSaints"])
client = GraphBranchSaintClient()

import uuid

from fastapi.responses import StreamingResponse
import requests

# --------------------------------------------------
# CREATE saint WITHOUT image (application/json)
# --------------------------------------------------
@router.post("/", response_model=BranchSaintSingleRecordResponse)
def create_branch_saint(payload: BranchSaintCreate):

    # 1️⃣ Generate UUID for saint (permanent identity)
    saint_uuid = str(uuid.uuid4())
    print(f"Generated Saint UUID: {saint_uuid}")
    # 2️⃣ Prepare payload for SharePoint
    data = payload.model_dump()
    data.update({
        "SaintUUID": saint_uuid,
        "IsActive": True
    })

    # 3️⃣ Create saint list item
    item = client.create_saint_item(data)
    saint_id = int(item["id"])

    return {
        "success": True,
        "sharepoint_response": {"id": item.id, **item.fields},
    }


# --------------------------------------------------
# CREATE saint WITH image (multipart/form-data)
# --------------------------------------------------

@router.post("/with-image", response_model=BranchSaintSingleRecordResponse)
def create_branch_saint_with_image(
    payload: BranchSaintCreate = Depends(BranchSaintCreate.as_form),
    photo: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    validate_image(photo)

    # 1️ Generate UUID for saint (permanent identity)
    saint_uuid = str(uuid.uuid4())

    # 2️ Prepare payload for SharePoint
    data = payload.model_dump()
    data.update({
        "SaintUUID": saint_uuid,
        "IsActive": True
    })

    # 3️ Create saint list item
    item = client.create_saint_item(data)
    saint_id = int(item["id"])

    # 4 Background task: image upload + face registration
    background_tasks.add_task(
        client.upload_saint_photo_background,
        saint_id=saint_id,
        item=item,
        file=photo,
    )
     # 5 Background task: qr image generation + upload + update list column
    background_tasks.add_task(
        client.upload_qr_image_pdf_background,
        saint_id=saint_id,
        item=item,
    )

    # Fetch latest item data
    item = client.get_saint_item_by_id(saint_id)

    # Return response
    return {
        "success": True,
        "sharepoint_response": {
            "id": saint_id,
            "SaintUUID": saint_uuid,
            **item["fields"],
        },
    }


# --------------------------------------------------
# GET all saints
# --------------------------------------------------
@router.get("/", response_model=list[BranchSaintSingleRecordResponse])
def list_branch_saints():
    items = client.get_saint_items()
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

@router.get("/search", response_model=BranchSaintMultiRecordsResponse)
def search_branch_saints(
    FullName: Optional[str] = Query(None),
    Gender: Optional[str] = Query(None),
    AgeFrom: Optional[int] = Query(None),
    AgeEnd: Optional[int] = Query(None),
    City: Optional[str] = Query(None),
):
    filters = {}

    if FullName is not None:
        filters["Title"] = FullName

    if Gender is not None:
        filters["Gender"] = Gender

    if AgeFrom is not None and AgeEnd is not None:
        filters["AgeMin"] >= AgeFrom and filters["AgeMax"] <= AgeEnd
        
    if City is not None:
        filters["City"] = City
    items = client.get_saint_items(filters=filters or None)

    # 🔑 Convert SPListItem → dict
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
        "sharepoint_response": response_items,
    }

@router.get("/search/paginated", response_model=BranchSaintMultiRecordsResponse)
def search_branch_saints_paginated(
    FullName: Optional[str] = Query(None),
    Gender: Optional[str] = Query(None),
    AgeFrom: Optional[int] = Query(None),
    AgeEnd: Optional[int] = Query(None),
    City: Optional[str] = Query(None),
    page_size: int = Query(20, le=100),
    cursor: Optional[str] = Query(None),
):
    filters = {}

    if FullName:
        filters["Title"] = FullName

    if Gender:
        filters["Gender"] = Gender

    if City:
        filters["City"] = City

    # ⚠ SharePoint does NOT support range filters well
    # Best practice: post-filter in API
    result = client.get_saint_items_paginated(
        filters=filters or None,
        page_size=page_size,
        next_link=cursor,
    )

    items = result["items"]

    # Post-filter age range
    if AgeFrom is not None and AgeEnd is not None:
        items = [
            i for i in items
            if AgeFrom <= i.fields.get("Age", 0) <= AgeEnd
        ]

    response_items = [
        {
            "id": item.id,
            **item.fields
        }
        for item in items
    ]
    print(f"Returning {len(response_items)} items, next_cursor: {result['next_cursor']}")
    return {
        "success": True,
        "count": len(response_items),
        "next_cursor": result["next_cursor"],  # 👈 IMPORTANT
        "sharepoint_response": response_items,
    }


# --------------------------------------------------
# GET saint by ID
# --------------------------------------------------
@router.get("/{saint_id}", response_model=BranchSaintSingleRecordResponse)
def get_branch_saint(saint_id: int):
    try:
        item = client.get_saint_item_by_id(saint_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Saint not found")

    return {
        "success": True,
        "sharepoint_response": {
            "id": item["id"],
            **item["fields"],
        },
    }



# --------------------------------------------------
# UPDATE saint
# --------------------------------------------------
@router.put("/{saint_id}")
def update_branch_saint(saint_id: int, payload: BranchSaintUpdate):
    client.update_saint_item(
        saint_id, payload.model_dump(exclude_none=True)
    )
    return {"status": "updated"}


# --------------------------------------------------
# DELETE saint
# --------------------------------------------------
@router.delete("/{saint_id}")
def delete_branch_saint(saint_id: int):
    client.delete_saint_item(saint_id)
    return {"status": "deleted"}

# --------------------------------------------------

@router.get("/metadata/choices")
def get_branch_saint_choices():
    try:
        choices = client.get_choice_columns()
        return {
            "success": True,
            "choices": choices
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# --------------------------------------------------
# GET saint by QR UUID

@router.get("/qr/{saint_uuid}", response_model=BranchSaintSingleRecordResponse)
def get_saint_by_qr(saint_uuid: str):
    filters = {
        "SaintUUID": saint_uuid,
        #"IsActive": True
    }

    items = client.get_saint_items(filters=filters)

    if not items:
        raise HTTPException(status_code=404, detail="Invalid or inactive QR")

    saint = items[0]

    return {
        "success": True,
        "sharepoint_response": {
            "id": saint.id,
            **saint.fields
        }
    }
# --------------------------------------------------

# --------------------------------------------------
# GET saint phot by file name and saint id
# --------------------------------------------------
@router.get("/{saint_id}/photo")
def get_saint_photo(saint_id: int, filename: str):
    try:
        stream = client.download_saint_file_stream(
            saint_id=saint_id,
            filename=filename
        )

        return StreamingResponse(
            stream,
            media_type="image/jpeg",
            headers={"Content-Disposition": "inline"}
        )
       
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
@router.get("/{saint_id}/qr-image")
def get_saint_qr_image(saint_id: int, filename: str):
    try:
        stream = client.download_saint_file_stream(
            saint_id=saint_id,
            filename=filename
        )

        return StreamingResponse(
            stream,
            media_type="image/png",
            headers={"Content-Disposition": "inline"}
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{saint_id}/qr-pdf")
def get_saint_qr_pdf(
        saint_id: int,
        filename: str,
        request: Request   # 👈 FastAPI injects this automatically
):
    try:

        # pass request here to construct absolute URL for QR PDF 
        pdf_url = get_saint_qr_pdf_link(request, saint_id, filename)

        stream = client.download_saint_file_stream(
            saint_id=saint_id,
            filename=filename
        )

        return StreamingResponse(
            stream,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "inline;",
                "X-File-Url": pdf_url # 👈 Custom header to provide the absolute URL of the PDF
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    

def get_saint_qr_pdf_link(request: Request, saint_id: int, filename: str) -> str:
    base_url = str(request.base_url).rstrip("/")
    return f"{base_url}/branch-saints/{saint_id}/qr-pdf?filename={filename}"

