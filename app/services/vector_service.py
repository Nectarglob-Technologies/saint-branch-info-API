import faiss
import numpy as np
import os
import json
import hashlib
from typing import Dict

DIM = 512
DATA_DIR = "data"
INDEX_PATH = f"{DATA_DIR}/faces.index"
META_PATH = f"{DATA_DIR}/faces_meta.json"

os.makedirs(DATA_DIR, exist_ok=True)


def _id_to_int(value: str) -> int:
    return int(hashlib.sha1(value.encode()).hexdigest(), 16) % (2**63)


class VectorService:
    def __init__(self):
        if os.path.exists(INDEX_PATH):
            self.index = faiss.read_index(INDEX_PATH)
        else:
            self.index = faiss.IndexIDMap(faiss.IndexFlatIP(DIM))

        if os.path.exists(META_PATH):
            with open(META_PATH, "r") as f:
                self.meta = json.load(f)
        else:
            self.meta = {}

    def _save(self):
        faiss.write_index(self.index, INDEX_PATH)
        with open(META_PATH, "w") as f:
            json.dump(self.meta, f, indent=2)

    def add_face(
        self,
        embedding: np.ndarray,
        entity_type: str,
        entity_id: int,
        image_url: str,
    ):
        embedding = embedding.reshape(1, -1).astype("float32")
        faiss.normalize_L2(embedding)

        vector_id = _id_to_int(f"{entity_type}:{entity_id}")

        self.index.add_with_ids(
            embedding,
            np.array([vector_id], dtype="int64"),
        )

        self.meta[str(vector_id)] = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "image_url": image_url,
        }

        self._save()

    def search(self, embedding: np.ndarray, top_k: int = 20):
        if self.index.ntotal == 0:
            return {"high": [], "medium": [], "low": []}

        embedding = embedding.reshape(1, -1).astype("float32")
        faiss.normalize_L2(embedding)

        scores, ids = self.index.search(embedding, top_k)

        buckets = {"high": [], "medium": [], "low": []}

        for score, vid in zip(scores[0], ids[0]):
            if vid == -1:
                continue

            meta = self.meta.get(str(int(vid)))
            if not meta:
                continue

            record = {
                **meta,
                "score": float(score),
                "match_percentage": self._score_to_percentage(score),
            }

            if score >= 0.80:
                buckets["high"].append(record)
            elif score >= 0.65:
                buckets["medium"].append(record)
            elif score >= 0.50:
                buckets["low"].append(record)

        return buckets

    
    def _score_to_percentage(self, score: float) -> int:
        """
        Convert cosine similarity score to human readable %
        """
        if score < 0.50:
            return int(score * 100)

        normalized = (score - 0.50) / 0.50
        return min(100, int(round(50 + normalized * 50)))

