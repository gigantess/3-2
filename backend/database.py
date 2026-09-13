import os
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.config import FIREBASE_SERVICE_ACCOUNT_JSON, FIREBASE_PROJECT_ID, USE_MOCK_DB, BASE_DIR

logger = logging.getLogger("backend.database")

# In-Memory Database for local testing / mock mode
class MockCollection:
    def __init__(self, name: str, base_dir: Path):
        self.name = name
        self.storage_dir = base_dir / ".mock_db"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.storage_dir / f"{name}.json"
        self._docs: Dict[str, Dict[str, Any]] = self._load()

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self._docs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to persist mock db {self.name}: {e}")

    def document(self, doc_id: Optional[str] = None):
        if not doc_id:
            doc_id = str(uuid.uuid4())
        return MockDocumentReference(self, doc_id)

    def add(self, data: Dict[str, Any]):
        doc_id = str(uuid.uuid4())
        data_copy = dict(data)
        self._docs[doc_id] = data_copy
        self._save()
        return (None, MockDocumentReference(self, doc_id))

    def stream(self):
        # Re-read to reflect external changes
        self._docs = self._load()
        for doc_id, data in list(self._docs.items()):
            yield MockDocumentSnapshot(doc_id, dict(data))

    def where(self, field: str, op: str, value: Any):
        return self

    def order_by(self, field: str, direction=None):
        return self

    def limit(self, count: int):
        return self

class MockDocumentSnapshot:
    def __init__(self, doc_id: str, data: Dict[str, Any]):
        self.id = doc_id
        self._data = data
        self.exists = data is not None

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data) if self._data else {}

class MockDocumentReference:
    def __init__(self, collection: MockCollection, doc_id: str):
        self.collection = collection
        self.id = doc_id

    def get(self) -> MockDocumentSnapshot:
        self.collection._docs = self.collection._load()
        data = self.collection._docs.get(self.id)
        return MockDocumentSnapshot(self.id, data)

    def set(self, data: Dict[str, Any], merge: bool = False):
        if merge and self.id in self.collection._docs:
            self.collection._docs[self.id].update(data)
        else:
            self.collection._docs[self.id] = dict(data)
        self.collection._save()

    def update(self, data: Dict[str, Any]):
        if self.id in self.collection._docs:
            self.collection._docs[self.id].update(data)
            self.collection._save()
        else:
            raise KeyError(f"Document {self.id} not found")

    def delete(self):
        if self.id in self.collection._docs:
            del self.collection._docs[self.id]
            self.collection._save()

class MockFirestoreClient:
    def __init__(self, base_dir: Path = BASE_DIR):
        self.base_dir = base_dir
        self._collections: Dict[str, MockCollection] = {}
        logger.info("[MockDB] Initialized File-Backed Firestore Mock Client")

    def collection(self, name: str) -> MockCollection:
        if name not in self._collections:
            self._collections[name] = MockCollection(name, self.base_dir)
        return self._collections[name]


db_client = None

def get_db():
    global db_client
    if db_client is not None:
        return db_client

    if not USE_MOCK_DB:
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore

            if not firebase_admin._apps:
                cred = None
                creds_file = BASE_DIR / "firebase-credentials.json"
                if creds_file.exists():
                    cred = credentials.Certificate(str(creds_file))
                elif FIREBASE_SERVICE_ACCOUNT_JSON:
                    if os.path.exists(FIREBASE_SERVICE_ACCOUNT_JSON):
                        cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_JSON)
                    else:
                        parsed = json.loads(FIREBASE_SERVICE_ACCOUNT_JSON)
                        cred = credentials.Certificate(parsed)

                if cred:
                    firebase_admin.initialize_app(cred, {"projectId": FIREBASE_PROJECT_ID} if FIREBASE_PROJECT_ID else None)
                else:
                    firebase_admin.initialize_app()

            db_client = firestore.client()
            logger.info("Successfully connected to Google Cloud Firestore!")
            return db_client
        except Exception as e:
            logger.warning(f"Failed to initialize Firestore ({e}). Falling back to In-Memory Mock DB.")

    db_client = MockFirestoreClient()
    return db_client

def reset_db_client_for_testing():
    global db_client
    db_client = MockFirestoreClient()
    return db_client
