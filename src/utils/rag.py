import json
import os

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL = None
INDEX_FILE = "data/faiss.index"
DOC_STORE = "data/kb_chunks.jsonl"


def _ensure_model():
    global MODEL
    if MODEL is None:
        MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return MODEL


def build_index():
    os.makedirs("data/kb_docs", exist_ok=True)
    # collect chunks
    chunks = []
    for fn in sorted(os.listdir("data/kb_docs")):
        path = os.path.join("data/kb_docs", fn)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().strip()
        if not text:
            continue
        parts = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not parts:
            parts = [text]
        for i, p in enumerate(parts):
            chunks.append({"id": f"{fn}#{i}", "text": p, "source": fn})
    # save chunks
    with open(DOC_STORE, "w", encoding="utf-8") as out:
        for c in chunks:
            out.write(json.dumps(c, ensure_ascii=False) + "\n")
    if not chunks:
        return 0
    # embed
    model = _ensure_model()
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings).astype("float32"))
    faiss.write_index(index, INDEX_FILE)
    return len(chunks)


def retrieve(query, k=3):
    if not os.path.exists(INDEX_FILE) or not os.path.exists(DOC_STORE):
        raise RuntimeError(
            "Index not found — run build_index() after adding docs into data/kb_docs/"
        )
    model = _ensure_model()
    emb = model.encode([query], convert_to_numpy=True).astype("float32")
    index = faiss.read_index(INDEX_FILE)
    D, I = index.search(emb, k)
    results = []
    with open(DOC_STORE, "r", encoding="utf-8") as f:
        chunks = [json.loads(l) for l in f]
    for idx in I[0]:
        if 0 <= idx < len(chunks):
            results.append(chunks[idx])
    return results
