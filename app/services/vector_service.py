import faiss
import numpy as np
import os
import json
import hashlib
import threading
from typing import Dict

from azure.core.exceptions import ResourceNotFoundError
from app.services.blob_service import BlobVectorStorage

DIM = 512

DATA_DIR = "data"
INDEX_PATH = f"{DATA_DIR}/faces.index"
META_PATH = f"{DATA_DIR}/faces_meta.json"

os.makedirs(DATA_DIR, exist_ok=True)


def _id_to_int(value: str) -> int:
    return int(hashlib.sha1(value.encode()).hexdigest(), 16) % (2**63)


class VectorService:
    """
    FAISS + Azure Blob integrated vector service
    """

    _lock = threading.Lock()

    def __init__(self):
        print("VectorService instance:", id(self)) # add  for check msg
        self.storage = BlobVectorStorage()
        self.index_etag = None
        self._load_from_blob_or_local()

    # ---------------------------------------------------
    # INITIAL LOAD (SAFELY HANDLED)
    # ---------------------------------------------------
    def _load_from_blob_or_local(self):
        print("\n🔹 Loading Vector DB (Blob or Local)")


        blob_loaded = False

        try:
            self.index_etag = self.storage.download_file(
                "faces.index", INDEX_PATH
            )

            self.storage.download_file(
                "faces_meta.json", META_PATH
            )

            print("✅ Vector DB downloaded from Blob")
            blob_loaded = True

        except ResourceNotFoundError:
            print("⚠ Blob files not found. Creating new index.")
        except Exception as e:
            print(f"⚠ Blob load failed: {e}")

        # ---------------------------
        # SAFE FAISS LOAD
        # ---------------------------
        try:
            if blob_loaded and os.path.exists(INDEX_PATH) and os.path.getsize(INDEX_PATH) > 0:
                self.index = faiss.read_index(INDEX_PATH)
                print("✅ FAISS index loaded successfully")
            else:
                self.index = faiss.IndexIDMap(
                    faiss.IndexFlatIP(DIM)
                )
                print("⚠ Created new empty FAISS index")


        except Exception:
            print("⚠ Corrupted index detected. Creating new index.")
            self.index = faiss.IndexIDMap(
                faiss.IndexFlatIP(DIM)
            )
        print("📊 Current vectors in index:", self.index.ntotal)

        # ---------------------------
        # SAFE METADATA LOAD
        # ---------------------------
        try:
            if blob_loaded and os.path.exists(META_PATH) and os.path.getsize(META_PATH) > 0:
                with open(META_PATH, "r") as f:
                    self.meta = json.load(f)
                print("✅ Metadata loaded")
            else:
                self.meta = {}
        except Exception:
            print("⚠ Corrupted metadata detected. Resetting metadata.")
            self.meta = {}

    # ---------------------------------------------------
    # SAVE (LOCAL + BLOB SAFE)
    # ---------------------------------------------------
    def _save(self):

        print("\n🔹 Saving Vector DB")

        # Save locally
        faiss.write_index(self.index, INDEX_PATH) # save faiss index to local file
        print("💾 FAISS index saved locally")
        


        #This saves metadata information in a JSON file.
        with open(META_PATH, "w") as f:
            json.dump(self.meta, f, indent=2)
        print("💾 Metadata saved locally")

        # Upload safely
        # This uploads the vector index file to Azure Blob Storage.
        try:
            print("⬆ Uploading Vector DB to Blob...")
            self.storage.upload_file(
                "faces.index",
                INDEX_PATH,
                etag=self.index_etag #multiple users conflict The ETag is used to prevent conflicts.
            )

            # Refresh ETag after successful upload
            self.index_etag = self.storage.download_file(
                "faces.index",
                INDEX_PATH
            )

            self.storage.upload_file(
                "faces_meta.json",
                META_PATH
            )

            print("✅ Vector DB uploaded to Blob")
            self._load_from_blob_or_local()
            # print("Vectors available for search:", self.index.ntotal)

        except Exception as e:
            raise Exception(
                f"Vector DB update conflict. Retry operation. {e}"
            )

    # ---------------------------------------------------
    # ADD FACE (REGISTER OR UPDATE)
    # ---------------------------------------------------
    def add_face(
        self,
        embedding: np.ndarray,
        entity_type: str,
        entity_id: int,
        image_url: str,
    ):

        with self._lock:

            embedding = embedding.reshape(1, -1).astype("float32")
            faiss.normalize_L2(embedding)

            vector_id = _id_to_int(f"{entity_type}:{entity_id}")

            # Remove existing vector (safe update behavior)
            self.index.remove_ids(
                np.array([vector_id], dtype="int64")
            )

            self.index.add_with_ids(
                embedding,
                np.array([vector_id], dtype="int64"),
            )
            print("Vector added for:", entity_id)
            print("Total vectors:", self.index.ntotal)

            self.meta[str(vector_id)] = {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "image_url": image_url,
            }

            self._save()

    # ---------------------------------------------------
    # EXPLICIT IMAGE UPDATE METHOD (SAFE)
    # ---------------------------------------------------
    def update_face_embedding(
        self,
        embedding: np.ndarray,
        entity_type: str,
        entity_id: int,
        image_url: str,
    ):
        """
        Explicit method for image replacement.
        Does NOT change existing functionality.
        """

        with self._lock:

            #print(f"Updating embedding for {entity_type}:{entity_id}")

            embedding = embedding.reshape(1, -1).astype("float32")
            faiss.normalize_L2(embedding)

            vector_id = _id_to_int(f"{entity_type}:{entity_id}")

            # Remove old embedding
            self.index.remove_ids(
                np.array([vector_id], dtype="int64")
            )

            # Add new embedding
            self.index.add_with_ids(
                embedding,
                np.array([vector_id], dtype="int64"),
            )

            # Update metadata
            self.meta[str(vector_id)] = {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "image_url": image_url,
            }

            self._save()

            print("✅ Embedding updated successfully")

    # ---------------------------------------------------
    # SEARCH (UNCHANGED)
    # ---------------------------------------------------
    def search(self, embedding: np.ndarray, top_k: int = 20):

        print(f"Performing search. Index total vectors: {self.index.ntotal}")
        if self.index.ntotal == 0:
            return {"high": [], "medium": [], "low": []}

        embedding = embedding.reshape(1, -1).astype("float32")
        faiss.normalize_L2(embedding)

        scores, ids = self.index.search(embedding, top_k)
        print(f"Search scores in vector_service: {scores}, IDs: {ids}")
       

        buckets = {"high": [], "medium": [], "low": []}

        for score, vid in zip(scores[0], ids[0]):
            #print(f"Raw search result - ID: {vid}, Score: {score:.4f}")
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
            #print(f"Search result - ID: {vid}, Score: {score:.4f}, Meta: {meta}")
            if score >= 0.80:
                buckets["high"].append(record)
            elif score >= 0.65:
                buckets["medium"].append(record)
            elif score >= 0.50:
                buckets["low"].append(record)
        print(f"Bucketed search results: {buckets}")
        
        return buckets

    # ---------------------------------------------------
    def _score_to_percentage(self, score: float) -> int:
        if score < 0.50:
            return int(score * 100)

        normalized = (score - 0.50) / 0.50
        return min(100, int(round(50 + normalized * 50)))
    
    # Global singleton instance
vector_service_instance = VectorService()
