import requests
from urllib.parse import urlparse
from typing import List, Dict, Optional

from app.core.security import GraphAuth
from app.core.config import settings
from app.utils.image import resize_image
from app.services.face_service import FaceService
from app.utils.image import resize_image
from fastapi import UploadFile
from app.models.sp_branch_saint_item import SPListItem
from app.utils.sharepoint_uploader import SharePointUploader
from app.utils.qr import generate_qr
from app.utils.pdf import generate_qr_pdf_card

import json


class GraphBranchSaintClient:
    def __init__(self):
        self.auth = GraphAuth()
        self.face_service = FaceService()

        # Microsoft Graph base URL
        self.graph_base = "https://graph.microsoft.com/v1.0"

        # Resolve and cache IDs once
        self.site_id = self._get_site_id(settings.SITE_URL)
        self.list_id = self._get_list_id(settings.SAINT_LIST_NAME)
        self.saint_drive_id = self._get_doc_lib_drive_id(settings.SAINT_DOC_LIB)
        self.list_name = settings.SAINT_LIST_NAME
        self.site_url = settings.SITE_URL
        self.tenant_id = settings.TENANT_ID

        # Base URL for saint list operations
        self.base_url = (
            f"https://graph.microsoft.com/v1.0/sites/"
            f"{self.site_id}/lists/{self.list_id}"
        )

        self.uploader = SharePointUploader(
                graph_base=self.graph_base,
                site_id=self.site_id,
                drive_id=self.saint_drive_id,
                headers_binary=self._headers_binary(),
                tenant_id=self.tenant_id,
                base_url=self.base_url,
                headers=self._headers()
            )

    # ------------------------------------------------------------------
    # Headers
    # ------------------------------------------------------------------

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.auth.get_token()}",
            "Content-Type": "application/json",
        }

    def _headers_binary(self):
        return {
            "Authorization": f"Bearer {self.auth.get_token()}",
        }

    # ------------------------------------------------------------------
    # Resolve Graph IDs
    # ------------------------------------------------------------------

    def _get_site_id(self, site_url: str) -> str:
        parsed = urlparse(site_url)
        hostname = parsed.netloc
        site_path = parsed.path

        url = f"{self.graph_base}/sites/{hostname}:{site_path}"
        resp = requests.get(url, headers=self._headers())
        resp.raise_for_status()
        return resp.json()["id"]

    def _get_list_id(self, list_name: str) -> str:
        url = f"{self.graph_base}/sites/{self.site_id}/lists"
        resp = requests.get(url, headers=self._headers())
        resp.raise_for_status()

        for lst in resp.json()["value"]:
            if lst["displayName"] == list_name:
                return lst["id"]

        raise RuntimeError(f"List not found: {list_name}")

    def _get_doc_lib_drive_id(self, library_name: str) -> str:
        url = f"{self.graph_base}/sites/{self.site_id}/drives"
        resp = requests.get(url, headers=self._headers())
        resp.raise_for_status()

        for drive in resp.json()["value"]:
            if drive["name"] == library_name:
                return drive["id"]

        raise RuntimeError(f"Document library not found: {library_name}")
    
    def get_saint_items(
        self,
        filters: Optional[Dict] = None
    ) -> list[SPListItem]:
            
        url = f"{self.base_url}/items?expand=fields"
        params = {}
        if filters:
            params["$filter"] = self._build_filter_query(filters)
        
        resp = requests.get(
            url,
            headers={
            "Authorization": f"Bearer {self.auth.get_token()}",
            "Prefer": "HonorNonIndexedQueriesWarningMayFailRandomly",
        },
            params = params, timeout=30
        )
        resp.raise_for_status()
        #print("SAINT ITEMS RESPONSE: ",resp.json())
        return [SPListItem(**item) for item in resp.json()["value"]]
    
    def get_saint_items_paginated(
        self,
        filters: Optional[Dict] = None,
        page_size: int = 20,
        next_link: Optional[str] = None,
    ) -> list[SPListItem]:
        """
        Cursor-based pagination using Graph @odata.nextLink
        """

        if next_link:
            url = next_link
            params = None
        else:
            url = f"{self.base_url}/items"
            params = {
                "$expand": "fields",
                "$top": page_size
            }
            if filters:
                params["$filter"] = self._build_filter_query(filters)

        #print(f"Fetching paginated items from URL: {url} with params: {params}")

        resp = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {self.auth.get_token()}",
                "Prefer": "HonorNonIndexedQueriesWarningMayFailRandomly",
            },
            params=params,
            timeout=30,
        )
        resp.raise_for_status()

        data = resp.json()
        return {
            "items": [SPListItem(**item) for item in data.get("value", [])],
            "next_cursor": data.get("@odata.nextLink"),
        }


    # ---------------------------------------
    # GET SINGLE SAINT BY ID (BEST PRACTICE)
    # ---------------------------------------
    def get_saint_item_by_id(
        self,
        saint_id: int
    ) -> Dict:
        """
        Fetch single saint record directly by ID
        """
        url = (
            f"{self.base_url}/items/{saint_id}"
            "?expand=fields"
        )
        resp = requests.get(url, headers=self._headers(), timeout=30)

        if resp.status_code == 404:
            raise ValueError("Saint not found")
        
        resp.raise_for_status()

        return resp.json()
    
    # ---------------------------------------
    # INTERNAL FILTER BUILDER
    # ---------------------------------------    
    def _build_filter_query(self, filters: Dict) -> str:
        conditions = []

        for key, value in filters.items():
            field = f"fields/{key}"

            if isinstance(value, str):
                conditions.append(f"{field} eq '{value}'")
            elif isinstance(value, bool):
                conditions.append(f"{field} eq {str(value).lower()}")
            else:
                conditions.append(f"{field} eq {value}")

        return " and ".join(conditions)

    # ------------------------------------------------------------------
    # Saint CRUD (List only)
    # ------------------------------------------------------------------

    def create_saint_item(self, payload: dict) -> dict:
        url = (
            f"{self.base_url}/items"
        )
        print("Creating saint with payload:", payload)
        resp = requests.post(
            url,
            headers=self._headers(),
            json={"fields": payload},
        )
        resp.raise_for_status()
        return resp.json()

    def update_saint_item(self, item_id: int, payload: dict):
        url = (
            f"{self.base_url}/items/{item_id}/fields"
        )

        resp = requests.patch(
            url,
            headers=self._headers(),
            json=payload,
        )
        resp.raise_for_status()

    def delete_saint_item(self, item_id: int):
        url = (
            f"{self.base_url}/items/{item_id}"
        )

        resp = requests.delete(url, headers=self._headers())
        resp.raise_for_status()

    # ------------------------------------------------------------------
    # Background task: upload image + face registration
    # ------------------------------------------------------------------

    def upload_saint_photo_background(
        self,
        saint_id: int,
        item: dict,
        file: UploadFile,
    ):
        """
        Background task:
        1. Upload image to document library
        2. Register face embedding into vector DB
        """

        #try:

        # 1️⃣ Resize image
        resized_bytes = resize_image(file)
        #print("Resized image bytes size:", len(resized_bytes))
        
        # 2️⃣ Upload to SharePoint document library using SharePointUploader utility class - pass connection details
        
        saint_data = {
            "id": item["id"],
            **item.get("fields", {})
        }

        # Upload image file
        photo_url = self.uploader.upload_file(
            saint_id=saint_id,
            file_bytes=resized_bytes,
            filename=saint_data.get("SaintUUID") + file.filename[file.filename.rfind("."):],
        )
        
        # Update SaintPhoto column with server relative URL
        extacted_image_url = self.uploader.extract_server_relative_url(photo_url)
        
        # Update SaintPhoto column
        self.uploader.update_image_column(saint_id,"SaintPhoto",extacted_image_url)
        
        # Register face (detector + embedding + FAISS)
        self.face_service.register_face(
            entity_type="saint",
            entity_id=saint_id,
            image_bytes=resized_bytes,
            image_url=photo_url,
        )
        
        #except Exception as e:
            # Never crash FastAPI background task
        #    print(f"[ERROR] Saint photo and face registration background task failed: {e}")

    def upload_qr_image_pdf_background(
        self,
        saint_id: int,
        item: dict,
    ):
        """
        Background task:
        1. Upload qr image to document library
        2. Register face embedding into vector DB
        """
        print("Starting QR and PDF generation background task.")
        #try:
        # 4️⃣ Generate QR code and store in SharePoint list
        qr_path,qr_image_bytes = generate_qr(
            saint=item,
            uploader= self.uploader,
            ttl_days=30,
            column_name="QRImage"
        )

        # 5️⃣ Generate printable PDF Saint Card
        pdf_path = generate_qr_pdf_card(
            saint=item,
            qr_image_bytes=qr_image_bytes,
            uploader= self.uploader,
            column_name="PDFPath"
        )
            

        #except Exception as e:
            # Never crash FastAPI background task
        #    print(f"[ERROR] Saint image background task failed: {e}")


    def get_choice_columns(self) -> dict:
        """
        Fetch dropdown (Choice) columns using Microsoft Graph
        """
        url = (
            f"{self.base_url}"
            f"/columns"
        )

        resp = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {self.auth.get_token()}",
                "Accept": "application/json"
            },
            timeout=30
        )
        resp.raise_for_status()

        columns = resp.json()["value"]
        choices = {}

        for col in columns:
            if col.get("choice"):
                choices[col["name"]] = col["choice"]["choices"]

        return choices

     # --------------------------------------------------
    # DOCUMENT LIBRARY FILE FETCH (NEW – CORRECT WAY)
    # --------------------------------------------------

    def _build_saint_file_path(
        self,
        saint_id: int,
        filename: str
    ) -> str:
        """
        Example:
        Saint-116/photo.jpg
        """
        return f"/Saint-{saint_id}/{filename}"

    def download_saint_file_stream(
        self,
        saint_id: int,
        filename: str
    ):
        """
        Stream file bytes directly from document library
        """
        server_relative_path = self._build_saint_file_path(
            saint_id,
            filename
        )
        #print(f"Downloading file from SharePoint with server relative path: {server_relative_path}")
        graph_url = (
            f"{self.graph_base}"
            f"/sites/{self.site_id}"
            f"/drives/{self.saint_drive_id}"
            f"/root:{server_relative_path}:/content"
        )
        #print(f"Constructed Graph URL for file download: {graph_url}")
        resp = requests.get(
            graph_url,
            headers=self._headers_binary(),
            stream=True,
            timeout=30
        )

        if resp.status_code == 404:
            raise ValueError("File not found")

        resp.raise_for_status()
        return resp.iter_content(chunk_size=8192)
    

    def get_image_filename(item: dict, column_name: str = "SaintPhoto") -> str | None:
        """
        Extract fileName from SharePoint Image column
        """
        fields = item.get("fields", {})
        image_value = fields.get(column_name)

        if not image_value:
            return None

        try:
            image_json = json.loads(image_value)
            return image_json.get("fileName")
        except json.JSONDecodeError:
            return None
