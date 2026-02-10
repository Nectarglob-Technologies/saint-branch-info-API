import requests
import json
from urllib.parse import urlparse
from requests.exceptions import RequestException



class SharePointUploader:
    def __init__(self, graph_base, site_id, drive_id, headers_binary, headers,tenant_id):
        self.graph_base = graph_base
        self.site_id = site_id
        self.drive_id = drive_id
        self._headers_binary = headers_binary
        self.tenant_id = tenant_id.split("-")[0]
        self._headers = headers
    # ---------------- FILE UPLOAD ----------------
    def upload_file(
        self,
        saint_id: int,
        file_bytes: bytes,
        filename: str,
    ) -> str:
        folder = f"saint-{saint_id}"

        upload_url = (
            f"{self.graph_base}/sites/{self.site_id}"
            f"/drives/{self.drive_id}"
            f"/root:/{folder}/{filename}:/content"
        )

        try:
            resp = requests.put(
                upload_url,
                headers=self._headers_binary(),
                data=file_bytes,
                timeout=30,
            )
            resp.raise_for_status()

            return resp.json()["webUrl"]

        except RequestException as exc:
            self._raise_graph_error(
                exc,
                operation="upload_file",
                url=upload_url,
            )

    # ---------------- IMAGE COLUMN ----------------
    def update_image_column(self, item_id: int, image_column: str, image_url: str):
        image_json = {
            "type": "thumbnail",
            "fileName": image_url.split("/")[-1],
            "serverUrl": f"https://{self.tenant_id}.sharepoint.com",
            "serverRelativeUrl": image_url,
        }

        payload = {image_column: json.dumps(image_json)}
        url = f"{self.base_url}/items/{item_id}/fields"

        try:
            resp = requests.patch(url, json=payload, headers=self._headers(), timeout=30)
            resp.raise_for_status()

        except RequestException as exc:
            self._raise_graph_error(
                exc,
                operation="update_image_column",
                url=url,
                extra={"column": image_column},
            )

    # ---------------- TEXT COLUMN ----------------
    def update_text_column(self, item_id: int, column_name: str, value: str):
        payload = {column_name: value}
        url = f"{self.base_url}/items/{item_id}/fields"

        try:
            resp = requests.patch(url, json=payload, headers=self._headers(), timeout=30)
            resp.raise_for_status()

        except RequestException as exc:
            self._raise_graph_error(
                exc,
                operation="update_text_column",
                url=url,
                extra={"column": column_name},
            )

    # ---------------- HELPERS ----------------
    def extract_server_relative_url(self, web_url: str) -> str:
        parsed = urlparse(web_url)
        if not parsed.path:
            raise SharePointUploadError("Invalid SharePoint webUrl")
        return parsed.path

    def _raise_graph_error(self, exc, operation: str, url: str, extra: dict | None = None):
        status_code = None
        error_details = None

        if hasattr(exc, "response") and exc.response is not None:
            status_code = exc.response.status_code
            try:
                error_details = exc.response.json()
            except Exception:
                error_details = exc.response.text

        raise SharePointUploadError(
            message=f"SharePoint operation failed: {operation}",
            status_code=status_code,
            details={
                "url": url,
                "extra": extra,
                "graph_error": error_details,
            },
        ) from exc
