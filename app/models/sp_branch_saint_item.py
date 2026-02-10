from pydantic import BaseModel
from typing import Dict, Any, List


class SPListItem(BaseModel):
    """
    Represents a SharePoint List Item returned by Microsoft Graph
    """
    id: int | str
    fields: Dict[str, Any]

