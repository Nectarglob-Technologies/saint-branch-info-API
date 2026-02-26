from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List

class Settings(BaseSettings):
    # ---------------- Environment ----------------
    UI_ORIGINS: List[str] = []

    DEBUG: bool = Field(default=False)

    # ---------------- Azure / Graph ----------------
    TENANT_ID: str
    CLIENT_ID: str
    CLIENT_SECRET: str

    SITE_URL: str
    SAINT_LIST_NAME: str
    ATTENDANT_LIST_NAME: str
    SAINT_DOC_LIB: str
    ATTENDANT_DOC_LIB: str

    AZURE_STORAGE_CONNECTION_STRING: str

    class Config:
        env_file = ".env"
        #extra = "ignore"   # VERY IMPORTANT

settings = Settings()
