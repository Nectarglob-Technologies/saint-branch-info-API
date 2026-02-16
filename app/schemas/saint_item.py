from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from fastapi import Form

# ---------- CREATE ----------
class BranchSaintCreate(BaseModel):
   Title: str = "Avish"
   Gender: str = "Male"
   RegistrationID: str = "t-333"
   SaintContactNo: int = 88787
   Age: int = 33
   Height: int = 6
   Complexion: str = "normal"
   MentalHealth: str = "Good"
   SelfReliant: str = "Dependent"
   Address1: str = "test1"
   City: str = "Mumbai"
   State: str = "Maharashtra"
   Country: str = "India"
   Pincode: str = 87878
   BranchName: str = "Dadar"
   BranchAddress: str = "Mahim"
   EventIDLookupId: int = 2
   Comments: Optional[str] = "test commensts"

   # ✅ THIS IS REQUIRED
   @classmethod
   def as_form(
        cls,
        Title: str = Form(...),
        Gender: str = Form(...),
        RegistrationID: str = Form(...),
        SaintContactNo: int = Form(...),
        Age: int = Form(...),
        Height: int = Form(...),
        Complexion: str = Form(...),
        MentalHealth: str = Form(...),
        SelfReliant: str = Form(...),
        Address1: str = Form(...),
        City: str = Form(...),
        State: str = Form(...),
        Country: str = Form(...),
        Pincode: str = Form(...),
        BranchName: str = Form(...),
        BranchAddress: str = Form(...),
        EventIDLookupId: int = Form(...),
        Comments: Optional[str] = Form(None),
    ):
        return cls(
            Title=Title,
            Gender=Gender,
            RegistrationID=RegistrationID,
            SaintContactNo=SaintContactNo,
            Age=Age,
            Height=Height,
            Complexion=Complexion,
            MentalHealth=MentalHealth,
            SelfReliant=SelfReliant,
            Address1=Address1,
            City=City,
            State=State,
            Country=Country,
            Pincode=Pincode,
            BranchName=BranchName,
            BranchAddress=BranchAddress,
            EventIDLookupId=EventIDLookupId,
            Comments=Comments,
        )

    


# ---------- UPDATE ----------
class BranchSaintUpdate(BaseModel):
    Title: Optional[str] = None
    Gender: Optional[str] = None
    SaintContactNo: Optional[int] = None
    Age: Optional[int] = None
    Height: Optional[int] = None
    Complexion: Optional[str] = None
    MentalHealth: Optional[str] = None
    SelfReliant: Optional[str] = None
    Address1: Optional[str] = None
    City: Optional[str] = None
    State: Optional[str] = None
    Country: Optional[str] = None
    Pincode: Optional[str] = None
    BranchName: Optional[str] = None
    BranchAddress: Optional[str] = None
    EventIDLookupId: Optional[int] = None
    Comments: Optional[str] = None
    
# ---------- Single Record RESPONSE ----------
class BranchSaintSingleRecordResponse(BaseModel):
    success: bool
    sharepoint_response: Dict[str, Any]

# ---------- Multiple Record RESPONSE ----------
class BranchSaintMultiRecordsResponse(BaseModel):
    success: bool
    count: int
    next_cursor: Optional[str] = None
    sharepoint_response: List[Dict[str, Any]]