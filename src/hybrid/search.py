import hashlib
import math
import re
from pathlib import Path

DIM = 64
STOP = {"the", "a", "an", "is", "of", "and", "to", "in", "what", "why", "does", "how", "who", "when", "are", "be", "it", "at"}
ROOT = Path(__file__).resolve().parents[2]
MODES = {"hybrid", "bm25", "dense"}
K1 = 1.2
B = 0.75
RRF_K = 60
MIN_COVERAGE = 0.3


class SearchError(ValueError):
    pass


def stem(token):
    return token[:-1] if len(token) > 3 and token.endswith("s") and not token.endswith("ss") else token


def tokens(text):
    return [stem(token) for token in re.findall(r"[a-z0-9]+", text.lower()) if token not in STOP]


def embed(text):
    vector = [0.0] * DIM
    for token in tokens(text):
        digest = hashlib.sha256(token.encode()).digest()
        vector[digest[0] % DIM] += 1.0 if digest[1] % 2 == 0 else -1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def chunk(name, text):
    heading = None
    chunks = []
    lines = text.splitlines()
    start = None
    buffer = []

    def flush():
        if buffer:
            chunks.append({"source": name, "line": start, "heading": heading, "text": " ".join(buffer)})

    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            flush()
            buffer, start = [], None
            heading = stripped.lstrip("#").strip()
        elif not stripped:
            flush()
            buffer, start = [], None
        else:
            if start is None:
                start = number
            buffer.append(stripped)
    flush()
    return chunks


def load_corpus():
    passages = []
    for path in sorted((ROOT / "corpus").glob("*.md")):
        passages.extend(chunk(path.name, path.read_text(encoding="utf-8")))
    return passages


def bm25_scores(query, documents):
    doc_tokens = [tokens(document) for document in documents]
    count = len(doc_tokens)
    average = sum(len(items) for items in doc_tokens) / count if count else 0
    terms = set(tokens(query))
    df = {term: sum(term in items for items in doc_tokens) for term in terms}
    scores = []
    for items in doc_tokens:
        score = 0.0
        for term in terms:
            frequency = items.count(term)
            if not frequency:
                continue
            idf = math.log((count - df[term] + 0.5) / (df[term] + 0.5) + 1)
            score += idf * frequency * (K1 + 1) / (frequency + K1 * (1 - B + B * len(items) / average))
        scores.append(score)
    return scores


def rrf(rankings, k=RRF_K):
    fused = {}
    for ranking in rankings:
        for rank, key in enumerate(ranking, start=1):
            fused[key] = fused.get(key, 0.0) + 1 / (k + rank)
    return fused


def search(question, mode="hybrid", top_k=3, source=None):
    if not isinstance(question, str) or not question.strip():
        raise SearchError("question is empty")
    if mode not in MODES:
        raise SearchError(f"mode must be one of {', '.join(sorted(MODES))}")
    if not isinstance(top_k, int) or not 1 <= top_k <= 10:
        raise SearchError("top_k must be from 1 to 10")
    passages = load_corpus()
    if source is not None:
        if source not in {p["source"] for p in passages}:
            raise SearchError(f"unknown source: {source}")
        passages = [p for p in passages if p["source"] == source]

    texts = [p["text"] for p in passages]
    keyword = bm25_scores(question, texts)
    query = embed(question)
    dense = [sum(a * b for a, b in zip(query, embed(text))) for text in texts]
    by_bm25 = sorted(range(len(passages)), key=lambda i: (-keyword[i], i))
    by_dense = sorted(range(len(passages)), key=lambda i: (-dense[i], i))
    bm25_rank = {i: rank for rank, i in enumerate(by_bm25, start=1)}
    dense_rank = {i: rank for rank, i in enumerate(by_dense, start=1)}

    if mode == "bm25":
        order = by_bm25
        fused = {i: keyword[i] for i in order}
    elif mode == "dense":
        order = by_dense
        fused = {i: dense[i] for i in order}
    else:
        fused = rrf([[i for i in by_bm25 if keyword[i] > 0], [i for i in by_dense if dense[i] > 0]])
        for i in range(len(passages)):
            fused.setdefault(i, 0.0)
        order = sorted(fused, key=lambda i: (-fused[i], i))

    query_terms = set(tokens(question))
    hits = []
    for i in order[:top_k]:
        coverage = len(query_terms & set(tokens(texts[i]))) / len(query_terms) if query_terms else 0
        hits.append({
            **passages[i],
            "bm25": round(keyword[i], 4),
            "dense": round(dense[i], 4),
            "fused": round(fused[i], 6),
            "bm25_rank": bm25_rank[i],
            "dense_rank": dense_rank[i],
            "coverage": round(coverage, 4),
        })
    if not hits or hits[0]["bm25"] <= 0 or hits[0]["coverage"] < MIN_COVERAGE:
        return {"answered": False, "answer": "No document shares enough terms.", "citation": None, "mode": mode, "passages": hits}
    best = hits[0]
    return {
        "answered": True,
        "answer": best["text"],
        "citation": f"{best['source']}:{best['line']}",
        "mode": mode,
        "passages": hits,
    }
