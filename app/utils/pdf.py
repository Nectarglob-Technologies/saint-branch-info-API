from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from pathlib import Path
from io import BytesIO
from app.utils.sharepoint_uploader import SharePointUploader
from reportlab.lib.utils import ImageReader

# CR80 Credit Card Size (ISO Standard)
CREDIT_CARD_SIZE = (85.60 * mm, 53.98 * mm)


def generate_qr_pdf_card(
        saint: dict, 
        qr_image_bytes: bytes,
        uploader: SharePointUploader,
        column_name: str = "" ) -> str:
    """
    Generate Saint ID Card PDF and upload to SharePoint
    """
    saint_data = {
        "id": saint["id"],
        **saint.get("fields", {})
    }

    buffer = BytesIO()
    
    c = canvas.Canvas(buffer, pagesize=CREDIT_CARD_SIZE)

    width, height = CREDIT_CARD_SIZE

    # ---------------- HEADER ----------------
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width / 2, height - 6 * mm, "SAINT ID CARD")

    # ---------------- TEXT ------------------
    c.setFont("Helvetica", 8)
    c.drawString(6 * mm, height - 16 * mm, "Name:")
    c.setFont("Helvetica-Bold", 8)
    c.drawString(20 * mm, height - 16 * mm, saint_data.get("Title", ""))

    c.setFont("Helvetica", 8)
    c.drawString(6 * mm, height - 22 * mm, "Branch:")
    c.setFont("Helvetica-Bold", 8)
    c.drawString(20 * mm, height - 22 * mm, saint_data.get("BranchName", ""))

    c.setFont("Helvetica", 7)
    c.drawString(6 * mm, height - 28 * mm, "UUID:")
    c.drawString(20 * mm, height - 28 * mm,saint_data.get("SaintUUID")[:12] + "...")

    # ---------------- QR --------------------
    qr_buffer = BytesIO(qr_image_bytes)
    qr_image = ImageReader(qr_buffer)
    c.drawImage(
        qr_image,
        width - 26 * mm,
        6 * mm,
        width=20 * mm,
        height=20 * mm,
        preserveAspectRatio=True
    )

    # ---------------- FOOTER ----------------
    c.setFont("Helvetica-Oblique", 6)
    c.drawCentredString(
        width / 2,
        3 * mm,
        "Scan QR to verify authenticity"
    )

    c.showPage()
    c.save()

    buffer.seek(0)

    filename = f"{saint_data['SaintUUID']}.pdf"

    # Upload qr image file
    pdf_url = uploader.upload_file(             
        saint_id=saint_data.get("id", ""),
        file_bytes=buffer.read(),
        filename=filename,
    )

    # get server relative URL for qr image column
    extacted_image_url = uploader.extract_server_relative_url(pdf_url)

    # Update qr image column
    uploader.update_text_column(saint_data.get("id", ""),column_name,extacted_image_url)

    return pdf_url

   
