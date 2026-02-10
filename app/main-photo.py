import requests
import json

# --- Configuration ---

TENANT_ID="93411ca0-bc94-4917-b2f9-9bdbbed60724"
CLIENT_ID="a9dd79ee-6c67-4970-84df-42a747372d7c"
CLIENT_SECRET="Itv8Q~Y2rdbt_8mM4xdzDo1VmPJ_Nts0FnYLIcCI"


SITE_URL="https://nectarglov.sharepoint.com/sites/InternPractice"
SAINT_LIST_NAME="BranchSaintsData"
ATTENDANT_LIST_NAME="BranchAttendantData"
SAINT_DOC_LIB="BranchSaintImages"
ATTENDANT_DOC_LIB="BranchAttendantImages"

SITE_ID = "your-tenant.sharepoint.com,site-guid,web-guid"
LIST_ID = "your-list-guid"
ITEM_ID = "1"  # ID of the list item to update
COLUMN_INTERNAL_NAME = "ThumbnailColumnName" # Internal name of your Image column

def get_access_token():
    url = f"https://login.microsoftonline.com{TENANT_ID}/oauth2/v2.0/token"
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'client_credentials',
        'scope': 'https://graph.microsoft.com/.default'
    }
    response = requests.post(url, data=data)
    return response.json().get('access_token')

def update_sharepoint_thumbnail(file_path, file_name):
    token = get_access_token()
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    # 1. Upload File to SiteAssets (or any library)
    # Endpoint: /sites/{site-id}/drive/root:/{path}:/content
    upload_url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drive/root:/SiteAssets/{file_name}:/content"
    
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    upload_res = requests.put(upload_url, headers={'Authorization': f'Bearer {token}'}, data=file_content)
    if upload_res.status_code not in [200, 201]:
        return f"Upload failed: {upload_res.text}"
    
    file_metadata = upload_res.json()
    server_relative_url = file_metadata.get('webUrl').split('.com')[-1] # Extract relative path

    # 2. Construct Thumbnail JSON Metadata
    # SharePoint requires the image field to be a stringified JSON object
    image_json = {
        "type": "thumbnail",
        "fileName": file_name,
        "serverUrl": f"https://{TENANT_ID.split('-')[0]}.sharepoint.com", # Basic tenant URL
        "serverRelativeUrl": server_relative_url
    }

    # 3. Update the List Item Field
    update_url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/lists/{LIST_ID}/items/{ITEM_ID}/fields"
    payload = {
        COLUMN_INTERNAL_NAME: json.dumps(image_json)
    }

    patch_res = requests.patch(update_url, headers=headers, json=payload)
    
    if patch_res.status_code == 200:
        return "Thumbnail updated successfully!"
    else:
        return f"Update failed: {patch_res.text}"

# Example Usage
# result = update_sharepoint_thumbnail("local_image.jpg", "uploaded_thumbnail.jpg")
# print(result)
