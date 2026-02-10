from msal import ConfidentialClientApplication
from app.core.config import settings

class GraphAuth:
    def __init__(self):
        self.authority = f"https://login.microsoftonline.com/{settings.TENANT_ID}"
        self.scope = ["https://graph.microsoft.com/.default"]

        self.app = ConfidentialClientApplication(
            client_id=settings.CLIENT_ID,
            authority=self.authority,
            client_credential=settings.CLIENT_SECRET,
        )

    def get_token(self) -> str:
        token = self.app.acquire_token_for_client(scopes=self.scope)
        #print("Acquired token from MSAL: ",token)
        if "access_token" not in token:
            raise RuntimeError(f"Token error: {token}")

        return token["access_token"]
