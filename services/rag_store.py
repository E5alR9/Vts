r"""
📚 RAG 向量知識庫 (RAG Store)

- chromadb 持久化在 data/rag/chroma（原套件裝了 chromadb 卻完全沒用，這裡補上）
- 文件端與查詢端都走 services.embedder（本地 fastembed 主力 / Gemini 備援）
- 來源涵蓋：data/*.json 記憶 + knowledge/ 外部知識文件

介面：
    upsert_documents(ids, texts, metas)     # 建檔（scripts/ingest_rag.py 用）
    search(query, k=4) -> List[dict]        # 檢索：[{"text","score","metadata"}]
    search_multi(queries, k=4)              # 多查詢召回後去重
    rag_prompt_block(query, k=4) -> str     # 直接產生可注入 prompt 的片段
    stats() -> dict
"""

import os
import re
import threading
from typing import Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERSIST_DIR = os.path.join(BASE_DIR, "data", "rag", "chroma")
COLLECTION = "knowledge"

_lock = threading.Lock()
_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is not None:
        return _collection
    import chromadb
    os.makedirs(PERSIST_DIR, exist_ok=True)
    _client = chromadb.PersistentClient(path=PERSIST_DIR)
    try:
        _collection = _client.get_or_create_collection(
            name=COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
    except Exception:
        # 舊版 chromadb 不接受該 metadata 參數
        _collection = _client.get_or_create_collection(name=COLLECTION)
    return _collection


def upsert_documents(ids: List[str], texts: List[str], metas: Optional[List[dict]] = None) -> int:
    """嵌入並寫入（同 id 覆寫）。回傳實際寫入筆數。"""
    from services.embedder import embed_texts
    if not texts:
        return 0
    with _lock:
        col = _get_collection()
        vecs = embed_texts(texts)
        metas = metas or [{} for _ in texts]
        # chromadb metadata 只吃 bool/int/float/str
        safe_metas = []
        for m in metas:
            safe = {}
            for k, v in (m or {}).items():
                if isinstance(v, (bool, int, float, str)):
                    safe[k] = v
                elif v is not None:
                    safe[k] = str(v)[:500]
            safe_metas.append(safe)
        # 分批，避免單次過大
        step = 64
        for i in range(0, len(ids), step):
            col.upsert(
                ids=ids[i:i + step],
                documents=texts[i:i + step],
                embeddings=vecs[i:i + step],
                metadatas=safe_metas[i:i + step],
            )
        return len(ids)


def search(query: str, k: int = 4) -> List[Dict]:
    """向量相似度檢索，回傳依相關度排序的片段。"""
    if not query or not query.strip():
        return []
    from services.embedder import embed_one
    try:
        with _lock:
            col = _get_collection()
            if col.count() == 0:
                return []
            vec = embed_one(query)
            res = col.query(
                query_embeddings=[vec],
                n_results=max(1, min(k, 10)),
                include=["documents", "metadatas", "distances"],
            )
    except Exception as e:
        try:
            print(f"[RAG] 檢索失敗：{str(e)[:120]}")
        except Exception:
            pass
        return []

    out = []
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]
    for doc, meta, dist in zip(docs, metas, dists):
        if not doc:
            continue
        # cosine distance -> 相似度 (0~1)
        score = 1.0 - float(dist)
        out.append({"text": doc, "score": round(score, 4), "metadata": meta or {}})
    return out


def search_multi(queries: List[str], k: int = 4) -> List[Dict]:
    """多組查詢 -> 合併去重（依分數取前 k 筆）"""
    seen: Dict[str, dict] = {}
    for q in queries:
        for hit in search(q, k=k):
            key = hit["text"][:120]
            if key not in seen or hit["score"] > seen[key]["score"]:
                seen[key] = hit
    return sorted(seen.values(), key=lambda x: -x["score"])[:k]


def rag_prompt_block(query: str, k: int = 3, min_score: float = 0.15) -> str:
    """產生可直接拼進 system/user prompt 的【RAG 記憶檢索】段落；無命中回傳空字串。"""
    hits = [h for h in search(query, k=k) if h["score"] >= min_score]
    if not hits:
        return ""
    lines = []
    for i, h in enumerate(hits, 1):
        src = (h["metadata"] or {}).get("source", "")
        src_tag = f"（來源: {src}）" if src else ""
        body = re.sub(r"\s+", " ", h["text"]).strip()[:300]
        lines.append(f"{i}. {body}{src_tag}")
    return (
        "【RAG 記憶檢索（與本題最相關的過往記憶與知識，可引用但別生硬照唸）】\n"
        + "\n".join(lines)
    )


def stats() -> dict:
    try:
        with _lock:
            col = _get_collection()
            return {"count": col.count(), "path": PERSIST_DIR, "collection": COLLECTION}
    except Exception as e:
        return {"count": -1, "error": str(e)[:120], "path": PERSIST_DIR}


def reset() -> int:
    """清空重來（僅測試/重建時使用）"""
    global _collection
    with _lock:
        import chromadb
        client = chromadb.PersistentClient(path=PERSIST_DIR)
        try:
            client.delete_collection(COLLECTION)
            _collection = None
            return 1
        except Exception:
            return 0


if __name__ == "__main__":
    import json
    print(json.dumps(stats(), ensure_ascii=False, indent=2))
