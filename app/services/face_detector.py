import numpy as np
import cv2
from insightface.app import FaceAnalysis


class FaceDetector:
    def __init__(self):
        self.app = FaceAnalysis(
            name="buffalo_l",
            providers=["CPUExecutionProvider"],  # change to CUDA if needed
        )
        self.app.prepare(ctx_id=0, det_size=(640, 640))

    def detect(self, image_bytes: bytes):
        """
        Detect faces and return InsightFace Face objects
        (each has .embedding, .bbox, etc.)
        """
        image = self._bytes_to_image(image_bytes)
        faces = self.app.get(image)
        return faces

    def _bytes_to_image(self, image_bytes: bytes):
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("Invalid image data")

        return img
