import requests
import json
from urllib.parse import urlparse
from app.core.security import GraphAuth
from app.core.config import settings
from app.models.sp_branch_saint_item import SPListItem
from app.utils.image import resize_image
from typing import List, Dict, Optional
from urllib.parse import quote



class GraphSaintAttendantClient:
    def __init__(self):
        self.auth = GraphAuth()
        self.site_id = self._get_site_id(settings.SITE_URL)
        self.list_id = self._get_list_id(settings.ATTENDANT_LIST_NAME)
        self.attendant_drive_id = self._get_doc_lib_drive_id(settings.ATTENDANT_DOC_LIB)
        self.base_url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/lists/{self.list_id}"
        self.tenant_id = settings.TENANT_ID.split('-')[0]

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.auth.get_token()}",
            "Content-Type": "application/json",
        }
    
    
    def _get_site_id(self, site_url: str) -> str:
        parsed = urlparse(site_url)
        url = f"https://graph.microsoft.com/v1.0/sites/{parsed.netloc}:{parsed.path}"
        return requests.get(url, headers=self._headers()).json()["id"]

    def _get_list_id(self, list_name: str) -> str:
        url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/lists"
        lists = requests.get(url, headers=self._headers()).json()["value"]
        for lst in lists:
            if lst["displayName"] == list_name:
                return lst["id"]
        raise RuntimeError("List not found")

    # -------- CRUD -------- #

    def create_attendant(self, fields: dict) -> SPListItem:
        url = f"{self.base_url}/items"
        payload = {"fields": fields}
        resp = requests.post(url, json=payload, headers=self._headers())

        if not resp.ok:
            print(json.dumps(resp.json(), indent=2))
            print(fields)
            resp.raise_for_status()

        return SPListItem(**resp.json())

    # def get_attendants(self):
    #     url = f"{self.base_url}/items?expand=fields"
    #     resp = requests.get(url, headers=self._headers())
    #     resp.raise_for_status()
    #     return [SPListItem(**i) for i in resp.json()["value"]]
    def get_attendants(
        self,
        filters: Optional[Dict] = None
    ) -> list[SPListItem]:

        url = f"{self.base_url}/items"
        params = {
            "$expand": "fields"
        }

        if filters:
            params["$filter"] = self._build_filter_query(filters)

        resp = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {self.auth.get_token()}",
                "Prefer": "HonorNonIndexedQueriesWarningMayFailRandomly",
            },
            params=params,
            timeout=30
        )

        resp.raise_for_status()

        return [SPListItem(**item) for item in resp.json()["value"]]

    def get_attendants_paginated(
        self,
        filters: Optional[Dict] = None,
        page_size: int = 20,
        next_link: Optional[str] = None,
    ):

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

        resp = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {self.auth.get_token()}",
                "Prefer": "HonorNonIndexedQueriesWarningMayFailRandomly",
            },
            params=params,
            timeout=30
        )

        resp.raise_for_status()

        data = resp.json()

        return {
            "items": [SPListItem(**item) for item in data.get("value", [])],
            "next_cursor": data.get("@odata.nextLink"),
        }

    def download_attendant_file_stream(self, attendant_id: int, filename: str):

        folder = f"attendant-{attendant_id}"

        download_url = (
            f"https://graph.microsoft.com/v1.0/sites/{self.site_id}"
            f"/drives/{self.attendant_drive_id}"
            f"/root:/{folder}/{filename}:/content"
        )

        resp = requests.get(
            download_url,
            headers={
                "Authorization": f"Bearer {self.auth.get_token()}",
            },
            stream=True,
        )

        if resp.status_code == 404:
            raise ValueError("Photo not found")

        resp.raise_for_status()

        return resp.raw


    def update_attendant(self, item_id: int, fields: dict):
            url = f"{self.base_url}/items/{item_id}/fields"
            requests.patch(url, json=fields, headers=self._headers())

    def delete_attendant(self, item_id: int):
            url = f"{self.base_url}/items/{item_id}"
            requests.delete(url, headers=self._headers())

    def upload_attendant_photo_background(self, attendant_id: int, file):
            
            content = resize_image(file)

            folder = f"attendant-{attendant_id}"
            filename = "profile.jpg"

            upload_url = (
                f"https://graph.microsoft.com/v1.0/sites/{self.site_id}"
                f"/drives/{self.attendant_drive_id}"
                f"/root:/{folder}/{filename}:/content"
            )

            resp = requests.put(
                upload_url,
                headers={
                    "Authorization": f"Bearer {self.auth.get_token()}",
                    "Content-Type": file.content_type,
                },
                data=content,
            )
            resp.raise_for_status()

            uploaded = resp.json()
            image_url = self._extract_server_relative_url(uploaded["webUrl"])

            self.update_image_column(
                attendant_id,
                image_column="AttendantPhoto",
                image_url=image_url,
            )

            #except Exception as e:
            #    print("❌ Attendant image upload failed:", str(e))

    def _get_doc_lib_drive_id(self, doc_lib_name: str) -> str:
            """
            Get Drive ID for a SharePoint Document Library
            """
            url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives"

            resp = requests.get(url, headers=self._headers())
            resp.raise_for_status()

            for drive in resp.json()["value"]:
                if drive["name"] == doc_lib_name:
                    return drive["id"]

            raise RuntimeError(f"Document library not found: {doc_lib_name}")
        
    def _extract_server_relative_url(self, site_url: str) -> str:
            """
            Extracts SharePoint server-relative URL from full site URL.

            Example:
            https://tenant.sharepoint.com/sites/MySite
            -> /sites/MySite
            """
            parsed = urlparse(site_url)

            if not parsed.path:
                raise ValueError("Invalid SharePoint site URL")

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
            print(f"PATCH URL: {url}")
            resp = requests.patch(url, json=payload, headers=self._headers())
            
            if not resp.ok:
                print("❌ Failed to update image column")
                print("Status:", resp.status_code)
                try:
                    print("Error JSON:")
                    print(json.dumps(resp.json(), indent=2))
                except Exception:
                    print("Raw Response:")
                    print(resp.text)

            resp.raise_for_status()
        
        # ---------------------------------------
        # GET SINGLE SAINT BY ID (BEST PRACTICE)
        # ---------------------------------------
    def get_attendant_item_by_id(
            self,
            attendant_id: int
        ) -> Dict:
            """
            Fetch single saint record directly by ID
            """
            url = (
                f"{self.base_url}/items/{attendant_id}"
                "?expand=fields"
            )
            resp = requests.get(url, headers=self._headers(), timeout=30)

            if resp.status_code == 404:
                raise ValueError("Attendant not found")
            
            resp.raise_for_status()

            return resp.json()
        
        # ---------------------------------------
        # INTERNAL FILTER BUILDER
        # ---------------------------------------    
        # def _build_filter_query(self, filters: Dict) -> str:
        #     conditions = []

        #     for key, value in filters.items():
        #         field = f"fields/{key}"

        #         if isinstance(value, str):
        #             conditions.append(f"{field} eq '{value}'")
        #         elif isinstance(value, bool):
        #             conditions.append(f"{field} eq {str(value).lower()}")
        #         else:
        #             conditions.append(f"{field} eq {value}")
        #         final_query = " and ".join(conditions)
        #         print("FILTER QUERY:", final_query)

        #         return final_query
        #     return " and ".join(conditions)

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
