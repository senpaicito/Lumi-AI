import chromadb
import os
import uuid
import json
from datetime import datetime

class MemoryManager:
    def __init__(self):
        self.memory_dir = os.path.join("data", "memory")
        self.diary_dir = os.path.join(self.memory_dir, "diary")
        os.makedirs(self.memory_dir, exist_ok=True)
        os.makedirs(self.diary_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.memory_dir)

    def _get_user_file(self, user_id):
        return os.path.join(self.memory_dir, f"{user_id}.json")

    def get_user_profile(self, user_id):
        file_path = self._get_user_file(user_id)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            default_profile = {
                "author_id": str(user_id),
                "associated_name": "Stranger",
                "intimacy_level": 1,
                "shared_lore": [],
                "last_interaction": "",
                "last_dm_id": None,
                "engagement_enabled": False,
                "dynamic_state": {
                    "mood": 50, "mood_baseline": 50,
                    "energy": 50, "energy_baseline": 50,
                    "stress": 0, "stress_baseline": 0,
                    "decay_rate": 2.0
                }
            }
            self.save_user_profile(user_id, default_profile)
            return default_profile

    def save_user_profile(self, user_id, profile_data):
        file_path = self._get_user_file(user_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2)

    def _get_user_collection(self, user_id):
        return self.client.get_or_create_collection(name=f"user_{user_id}")

    def save_memory(self, role, content, user_id):
        if not content or len(content.strip()) < 5:
            return 
        collection = self._get_user_collection(user_id)
        doc_id = f"mem_{str(uuid.uuid4())}"
        timestamp = datetime.now().isoformat()
        collection.add(documents=[content], metadatas=[{"role": role, "timestamp": timestamp}], ids=[doc_id])

    def recall_memories(self, query, user_id, limit=5):
        try:
            collection = self._get_user_collection(user_id)
            if collection.count() == 0: return []
            results = collection.query(query_texts=[query], n_results=limit)
            memories = []
            if results['documents'] and len(results['documents'][0]) > 0:
                for i, doc in enumerate(results['documents'][0]):
                    role = results['metadatas'][0][i].get('role', 'Unknown')
                    memories.append(f"[{role}]: {doc}")
            return memories
        except Exception:
            return []

    def get_recent_ltm(self, user_id, limit=10):
        try:
            collection = self._get_user_collection(user_id)
            if collection.count() == 0: return []
            results = collection.get(limit=limit)
            return [f"[{meta.get('role')}]: {doc}" for doc, meta in zip(results['documents'], results['metadatas'])]
        except Exception:
            return []

    def save_diary_entry(self, user_id, entry_text):
        user_diary_path = os.path.join(self.diary_dir, str(user_id))
        os.makedirs(user_diary_path, exist_ok=True)
        file_name = f"diary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(os.path.join(user_diary_path, file_name), 'w', encoding='utf-8') as f:
            f.write(entry_text)

    def read_latest_diary(self, user_id):
        user_diary_path = os.path.join(self.diary_dir, str(user_id))
        if not os.path.exists(user_diary_path): return None
        files = sorted(os.listdir(user_diary_path), reverse=True)
        if not files: return None
        with open(os.path.join(user_diary_path, files[0]), 'r', encoding='utf-8') as f:
            return f.read()
