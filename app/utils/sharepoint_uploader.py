import requests, json
from urllib.parse import urlparse

class SharePointUploader:
    def __init__(self, graph_base, site_id, drive_id, headers_binary,headers,tenant_id, base_url):
        self.graph_base = graph_base
        self.site_id = site_id
        self.drive_id = drive_id
        self._headers_binary = headers_binary
        self.tenant_id = tenant_id.split('-')[0]
        self.base_url = base_url
        self._headers = headers

    def upload_file(
        self,
        saint_id: int,
        file_bytes: bytes,
        filename: str,
    ) -> str:
        """
        Upload any saint-related file to SharePoint document library.
        """

        folder = f"saint-{saint_id}"

        upload_url = (
            f"{self.graph_base}/sites/{self.site_id}"
            f"/drives/{self.drive_id}"
            f"/root:/{folder}/{filename}:/content"
        )

        resp = requests.put(
            upload_url,
            headers=self._headers_binary,
            data=file_bytes,
        )
        resp.raise_for_status()

        return resp.json()["webUrl"]
    
    #Extract relative path to store it in SHarePoint column(image)    
    def extract_server_relative_url(self, web_url: str) -> str:
        """
        Converts:
        https://tenant.sharepoint.com/sites/site/lib/file.jpg
        ->
        /sites/site/lib/file.jpg
        """
        parsed = urlparse(web_url)

        if not parsed.path:
            raise ValueError("Invalid SharePoint webUrl")

        return parsed.path
    
    #Image column helper for SharePoint list / Library    
    def update_image_column(self, item_id: int, image_column: str, image_url: str):
        image_json = {
            "type": "thumbnail",
            "fileName": image_url.split("/")[-1],
            "serverUrl": f"https://{self.tenant_id}.sharepoint.com",
            "serverRelativeUrl": image_url
        }

        payload = {
            image_column: json.dumps(image_json)
        }

        url = f"{self.base_url}/items/{item_id}/fields"
        resp = requests.patch(url, json=payload, headers=self._headers)
        resp.raise_for_status()

    def update_text_column(
        self,
        item_id: int,
        column_name: str,
        value: str,
    ):
        """
        Update a Single line / Multiple line text column
        """

        payload = {
            column_name: value
        }

        url = f"{self.base_url}/items/{item_id}/fields"

        resp = requests.patch(
            url,
            json=payload,
            headers=self._headers
        )

        resp.raise_for_status()
