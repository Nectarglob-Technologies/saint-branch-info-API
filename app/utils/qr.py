import qrcode, json, time
from pathlib import Path
from app.core.config import settings
from cryptography.fernet import Fernet
from io import BytesIO
from app.utils.sharepoint_uploader import SharePointUploader


SECRET_KEY = Fernet.generate_key()  # store in ENV
cipher = Fernet(SECRET_KEY)

def generate_qr(saint: dict, uploader: SharePointUploader, ttl_days: int = 30,column_name: str = "") -> str:

    # -------------------------
    # 1. Build encrypted payload
    # -------------------------
    saint_data = {
        "id": saint["id"],
        **saint.get("fields", {})
    }

    payload = {
        "uuid": saint_data.get("SaintUUID"),
        "exp": int(time.time()) + (ttl_days * 86400)
    }

    encrypted = cipher.encrypt(json.dumps(payload).encode())

    # -------------------------
    # 2. Generate QR in memory
    # -------------------------
    img = qrcode.make(encrypted.decode())

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # -------------------------
    # 3. Upload to SharePoint
    # -------------------------
    filename = f"{saint_data.get("SaintUUID")}.png"
    
    # Upload qr image file
    qr_image_url = uploader.upload_file(
        saint_id=saint_data.get("id"),
        file_bytes=buffer.read(),
        filename=filename,
    )

    # get server relative URL for qr image column
    extracted_image_url = uploader.extract_server_relative_url(qr_image_url)

    # Update qr image column
    uploader.update_image_column(saint_data.get("id"),column_name,extracted_image_url)

    return qr_image_url, buffer.getvalue()




def decode_qr_payload(encrypted_text: str) -> str:
    data = json.loads(cipher.decrypt(encrypted_text.encode()))
    
    if data["exp"] < int(time.time()):
        raise ValueError("QR expired")

    return data["uuid"]