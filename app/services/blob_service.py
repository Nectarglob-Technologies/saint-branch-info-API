import os
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
from app.core.config import settings

class BlobVectorStorage:

    def __init__(self):
        self.conn_str = settings.AZURE_STORAGE_CONNECTION_STRING
        self.container = "vector-index-db"

        self.client = BlobServiceClient.from_connection_string(self.conn_str)
        self.container_client = self.client.get_container_client(self.container)

    def download_file(self, blob_name: str, local_path: str):
        blob_client = self.container_client.get_blob_client(blob_name)

        with open(local_path, "wb") as f:
            data = blob_client.download_blob()
            f.write(data.readall())

        return blob_client.get_blob_properties().etag

    def upload_file(self, blob_name: str, local_path: str, etag=None):
        blob_client = self.container_client.get_blob_client(blob_name)

        with open(local_path, "rb") as data:
            blob_client.upload_blob(
                data,
                overwrite=True,
                if_match=etag  # concurrency control
            )
