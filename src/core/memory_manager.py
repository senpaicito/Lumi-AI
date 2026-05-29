import chromadb
import os
import uuid
import json
from datetime import datetime

class MemoryManager:
    def __init__(self):
        self.memory_dir = os.path.join("data", "memory")
        os.makedirs(self.memory_dir, exist_ok=True)
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
        
        collection.add(
            documents=[content],
            metadatas=[{"role": role, "timestamp": timestamp}],
            ids=[doc_id]
        )
        print(f"💾 Saved to {user_id}'s LTM: [{role}] {content[:30]}...")

    def recall_memories(self, query, user_id, limit=5):
        try:
            collection = self._get_user_collection(user_id)
            if collection.count() == 0:
                return []
                
            results = collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            memories = []
            if results['documents'] and len(results['documents'][0]) > 0:
                for i, doc in enumerate(results['documents'][0]):
                    meta = results['metadatas'][0][i]
                    role = meta.get('role', 'Unknown')
                    memories.append(f"[{role}]: {doc}")
            return memories
        except Exception as e:
            print(f"Memory Recall Error: {e}")
            return []

    def wipe_memory(self, user_id=None):
        if user_id:
            try:
                self.client.delete_collection(f"user_{user_id}")
            except Exception:
                pass
            profile_path = self._get_user_file(user_id)
            if os.path.exists(profile_path):
                os.remove(profile_path)
        else:
            for collection in self.client.list_collections():
                if collection.name.startswith("user_"):
                    self.client.delete_collection(collection.name)
            for file in os.listdir(self.memory_dir):
                if file.endswith('.json'):
                    os.remove(os.path.join(self.memory_dir, file))
