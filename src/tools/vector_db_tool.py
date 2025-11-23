"""
Vector Database Tool for ARK Agent AGI
Provides local vector storage and retrieval using FAISS and Sentence Transformers
"""

import json
import os
import pickle
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from tools.base import BaseTool
from utils.observability.logging_utils import log_event


class VectorDBTool(BaseTool):
    """
    Local Vector Database using FAISS and Sentence Transformers
    """

    def __init__(
        self,
        index_path: str = "data/vector_store.index",
        metadata_path: str = "data/vector_metadata.pkl",
        model_name: str = "all-MiniLM-L6-v2",
    ):
        super().__init__(name="vector_db", description="Store and retrieve knowledge using vector embeddings")
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.model_name = model_name
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        # Initialize model (lazy load could be better, but we'll load on init for now)
        log_event("VectorDBTool", "Loading embedding model...")
        self.model = SentenceTransformer(self.model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        # Initialize or load index
        self.index = None
        self.metadata = []  # List of dicts, index corresponds to FAISS ID
        self._load_index()

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute vector DB operations.
        
        Args:
            action (str): "add" or "search"
            texts (List[str]): Texts to add (for "add")
            metadatas (List[Dict]): Metadata for texts (for "add")
            query (str): Query text (for "search")
            k (int): Number of results (for "search", default 5)
        """
        action = kwargs.get("action")
        
        if action == "add":
            texts = kwargs.get("texts", [])
            metadatas = kwargs.get("metadatas", [])
            return self.add_texts(texts, metadatas)
        elif action == "search":
            query = kwargs.get("query", "")
            k = kwargs.get("k", 5)
            return self.search(query, k)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Add texts to the vector index
        """
        if not texts:
            return {"success": False, "error": "No texts provided"}
            
        if metadatas is None:
            metadatas = [{} for _ in texts]
            
        if len(texts) != len(metadatas):
            return {"success": False, "error": "Texts and metadatas must have same length"}

        try:
            embeddings = self.model.encode(texts)
            embeddings = np.array(embeddings).astype("float32")
            
            # Add to index
            self.index.add(embeddings)
            
            # Add metadata
            for i, text in enumerate(texts):
                meta = metadatas[i].copy()
                meta["text"] = text  # Store text in metadata for retrieval
                self.metadata.append(meta)
            
            # Save
            self._save_index()
            
            log_event("VectorDBTool", f"Added {len(texts)} documents to index")
            return {"success": True, "count": len(texts)}
            
        except Exception as e:
            log_event("VectorDBTool", f"Error adding texts: {e}")
            return {"success": False, "error": str(e)}

    def search(self, query: str, k: int = 5) -> Dict[str, Any]:
        """
        Search the vector index
        """
        if not query:
            return {"success": False, "error": "No query provided"}
            
        if self.index.ntotal == 0:
            return {"success": True, "results": []}

        try:
            embedding = self.model.encode([query])
            embedding = np.array(embedding).astype("float32")
            
            distances, indices = self.index.search(embedding, k)
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx != -1 and idx < len(self.metadata):
                    item = self.metadata[idx]
                    results.append({
                        "text": item.get("text", ""),
                        "metadata": {k: v for k, v in item.items() if k != "text"},
                        "score": float(distances[0][i])
                    })
            
            return {"success": True, "results": results}
            
        except Exception as e:
            log_event("VectorDBTool", f"Error searching: {e}")
            return {"success": False, "error": str(e)}

    def _load_index(self):
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, "rb") as f:
                    self.metadata = pickle.load(f)
                log_event("VectorDBTool", f"Loaded index with {self.index.ntotal} vectors")
            except Exception as e:
                log_event("VectorDBTool", f"Error loading index: {e}. Creating new one.")
                self._create_new_index()
        else:
            self._create_new_index()

    def _create_new_index(self):
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []
        log_event("VectorDBTool", "Created new index")

    def _save_index(self):
        try:
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, "wb") as f:
                pickle.dump(self.metadata, f)
        except Exception as e:
            log_event("VectorDBTool", f"Error saving index: {e}")

# Global instance
vector_db = VectorDBTool()
