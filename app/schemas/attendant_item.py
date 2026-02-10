from pydantic import BaseModel
from typing import Optional, Dict, Any
from fastapi import Form

# ---------- CREATE ----------
class BranchAttendantCreate(BaseModel):
    Title: str ="pooja"
    AttendantContactNo: int = 1111111111
    AttendantAddress: str = "nashik"
    BranchSaintsDataIDLookupId: int = 2
    #AttendantPhoto: 

  # ✅ THIS IS REQUIRED
  
    @classmethod
    def as_form(
        cls,
        Title: str = Form(...),
        AttendantContactNo: int = Form(...),
        AttendantAddress: str = Form(...),
        BranchSaintsDataIDLookupId: int = Form(...),
    ):
        return cls(
            Title=Title,
            AttendantContactNo=AttendantContactNo,
            AttendantAddress=AttendantAddress,
            BranchSaintsDataIDLookupId=BranchSaintsDataIDLookupId,
        )

# ---------- UPDATE ----------
class BranchAttendantUpdate(BaseModel):
    Title: Optional[str] = None
    AttendantContactNo: Optional[int] = None
    AttendantAddress: Optional[str] = None
    BranchSaintsDataIDLookupId: Optional[int] = None
    


class BranchAttendantResponse(BaseModel):
    success: bool
    sharepoint_response: Dict[str, Any]
