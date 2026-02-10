from pydantic import BaseModel

class FaceMatch(BaseModel):
    saint_id: int
    image_url: str
    score: float
