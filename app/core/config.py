# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    TENANT_ID: str
    CLIENT_ID: str
    CLIENT_SECRET: str

    SITE_URL: str

    SAINT_LIST_NAME: str
    ATTENDANT_LIST_NAME: str

    SAINT_DOC_LIB: str
    ATTENDANT_DOC_LIB: str

    DOMAIN_NAME: str
    TEST_DOMAIN_URL: str

    class Config:
        env_file = ".env"


settings = Settings()

