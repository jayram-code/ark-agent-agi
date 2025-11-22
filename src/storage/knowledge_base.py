"""
Knowledge Base Storage
- Indexes text files from data/kb_docs
- Uses SentenceTransformers + FAISS for semantic search
"""

import os
import glob
import json
import time
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

KB_DIR = "data/kb_docs"
KB_INDEX_PATH = "data/kb.index"
KB_STORE_PATH = "data/kb_store.jsonl"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

_MODEL = None


def _ensure_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(EMBED_MODEL_NAME)
    return _MODEL


def initialize_kb(force_rebuild=False):
    """
    Scans KB_DIR, chunks text, and builds FAISS index if not exists or forced.
    """
    if os.path.exists(KB_INDEX_PATH) and os.path.exists(KB_STORE_PATH) and not force_rebuild:
        return

    print(f"Building Knowledge Base from {KB_DIR}...")
    os.makedirs("data", exist_ok=True)

    docs = []
    # Read all .txt files
    for filepath in glob.glob(os.path.join(KB_DIR, "*.txt")):
        filename = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
            # Simple chunking by paragraphs
            chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
            for i, chunk in enumerate(chunks):
                docs.append({"source": filename, "chunk_id": i, "text": chunk})

    if not docs:
        print("No documents found in KB_DIR.")
        return

    model = _ensure_model()
    texts = [d["text"] for d in docs]
    embeddings = model.encode(texts, convert_to_numpy=True).astype("float32")

    # Create FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    # Save index
    faiss.write_index(index, KB_INDEX_PATH)

    # Save metadata
    with open(KB_STORE_PATH, "w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc) + "\n")

    print(f"KB built with {len(docs)} chunks.")


def search_kb(query: str, k: int = 3) -> List[Dict[str, Any]]:
    """
    Search the knowledge base for relevant chunks.
    """
    if not os.path.exists(KB_INDEX_PATH) or not os.path.exists(KB_STORE_PATH):
        initialize_kb()
        if not os.path.exists(KB_INDEX_PATH):
            return []

    model = _ensure_model()
    q_emb = model.encode([query], convert_to_numpy=True).astype("float32")

    index = faiss.read_index(KB_INDEX_PATH)
    D, I = index.search(q_emb, k)

    # Load docs (inefficient for huge KBs, but fine for this scale)
    with open(KB_STORE_PATH, "r", encoding="utf-8") as f:
        docs = [json.loads(line) for line in f]

    results = []
    for dist, idx in zip(D[0], I[0]):
        if 0 <= idx < len(docs):
            doc = docs[idx]
            results.append(
                {
                    "text": doc["text"],
                    "source": doc["source"],
                    "score": float(1.0 / (1.0 + dist)),  # Convert distance to similarity score
                }
            )

    return results
