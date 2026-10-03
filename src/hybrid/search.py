import hashlib
import math
import re
from pathlib import Path

DIM = 64
STOP = {"the", "a", "an", "is", "of", "and", "to", "in", "what", "why", "does"}
ROOT = Path(__file__).resolve().parents[2]

def words(text):
    return set(re.findall(r"[a-z0-9]+", text.lower())) - STOP

def embed(text):
    vector = [0.0] * DIM
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        digest = hashlib.sha256(token.encode()).digest()
        vector[digest[0] % DIM] += 1.0 if digest[1] % 2 == 0 else -1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]

def search(question):
    corpus = []
    for path in sorted((ROOT / "corpus").glob("*.md")):
        corpus.append((path.name, path.read_text()))
    query_words = words(question)
    query_vector = embed(question)
    hits = []
    for name, text in corpus:
        keyword = len(query_words & words(text)) / len(query_words) if query_words else 0
        cosine = sum(a * b for a, b in zip(query_vector, embed(text)))
        hits.append({"source": name, "text": text.strip(), "keyword": round(keyword, 4), "cosine": round(cosine, 4), "fused": round(0.5 * keyword + 0.5 * cosine, 4)})
    hits.sort(key=lambda row: row["fused"], reverse=True)
    best = hits[0]
    if best["keyword"] < 0.3:
        return {"answered": False, "answer": "No document shares enough terms.", "passages": hits}
    return {"answered": True, "answer": best["text"], "passages": hits}
