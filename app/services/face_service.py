from app.services.face_detector import FaceDetector
from app.services.vector_service import VectorService


class FaceService:
    def __init__(self):
        self.detector = FaceDetector()
        self.vector_service = VectorService()

    # ---------------- REGISTER FACE ---------------- #

    def register_face(
        self,
        entity_type: str,
        entity_id: int,
        image_bytes: bytes,
        image_url: str,
    ):
        faces = self.detector.detect(image_bytes)

        if not faces:
            raise ValueError("No face detected")

        # Best practice: choose highest confidence face
        face = max(faces, key=lambda f: f.det_score)

        embedding = face.embedding.astype("float32")

        self.vector_service.add_face(
            embedding=embedding,
            entity_type=entity_type,
            entity_id=entity_id,
            image_url=image_url,
        )

        return {
            "status": "registered",
            "entity_type": entity_type,
            "entity_id": entity_id,
        }

    # ---------------- VERIFY FACE ---------------- #

    def verify_face(self, image_bytes: bytes):
        faces = self.detector.detect(image_bytes)

        if not faces:
            return {
                "match": False,
                "reason": "No face detected",
            }

        face = max(faces, key=lambda f: f.det_score)
        embedding = face.embedding.astype("float32")

        buckets = self.vector_service.search(embedding)

        high = buckets["high"]
        medium = buckets["medium"]
        low = buckets["low"]

        # ✅ Auto accept if strong match exists
        if high:
            best = max(high, key=lambda x: x["score"])
            return {
                "match": True,
                "confidence": "HIGH",
                "best_match": best,
                "review_options": {
                    "medium": medium,
                    "low": low,
                },
            }

        # ⚠️ Ask user to review medium matches
        if medium:
            return {
                "match": False,
                "confidence": "MEDIUM",
                "reason": "No strong match found",
                "review_options": {
                    "medium": medium,
                    "low": low,
                },
            }

        return {
            "match": False,
            "confidence": "LOW",
            "reason": "Face not recognized",
        }

    def verify_face_with_policy(self, image_bytes: bytes, mode: str = "default"):
        faces = self.detector.detect(image_bytes)

        if not faces:
            return {
                "match": False,
                "reason": "No face detected",
            }

        face = max(faces, key=lambda f: f.det_score)
        embedding = face.embedding.astype("float32")

        results = self.vector_service.search(embedding)

        best_match = results["high"][0] if results["high"] else None

        response = {
            "best_match": best_match,
            "confidence": "high" if best_match else "none",
            "more_matches_available": bool(
                results["medium"] or results["low"]
            ),
        }

        if mode == "review":
            response["matches"] = results
            response["confidence_policy"] = {
                "high": ">= 80% (auto accept)",
                "medium": "65–80% (manual review)",
                "low": "50–65% (weak match)",
            }

        return response
