import chromadb
from chromadb.utils import embedding_functions
import os
from datetime import datetime
import uuid

class MemoryManager:
    def __init__(self):
        # Initialize persistent database in data/memory folder
        db_path = os.path.join("data", "memory")
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Use default lightweight embedding model (all-MiniLM-L6-v2)
        # This downloads a small model automatically on first run
        self.embed_fn = embedding_functions.DefaultEmbeddingFunction()
        
        self.collection = self.client.get_or_create_collection(
            name="conversation_history",
            embedding_function=self.embed_fn
        )

    def save_memory(self, role, content):
        """Saves a message to the vector database."""
        if not content or len(content.strip()) < 5:
            return # Don't save empty/tiny messages

        # We add a timestamp to the metadata
        timestamp = datetime.now().isoformat()
        
        self.collection.add(
            documents=[content],
            metadatas=[{"role": role, "timestamp": timestamp}],
            ids=[str(uuid.uuid4())]
        )
        print(f"💾 Saved to LTM: [{role}] {content[:30]}...")

    def recall_memories(self, query_text, n_results=3):
        """Searches past conversations for context relevant to the query."""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        # Format results for the LLM
        memories = []
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i]
                role = meta.get('role', 'Unknown')
                memories.append(f"[{role}]: {doc}")
                
        return memories

    def wipe_memory(self):
        """Deletes the collection (Factory Reset)."""
        self.client.delete_collection("conversation_history")
        self.collection = self.client.get_or_create_collection(
            name="conversation_history",
            embedding_function=self.embed_fn
        )
