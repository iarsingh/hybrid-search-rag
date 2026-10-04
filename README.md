# Hybrid Search RAG

Level: 7 — Intermediate RAG

Skills: Python, BM25, hashed embeddings, reciprocal rank fusion, citations

Markdown files in `corpus/` are split into paragraphs, each tagged with its file, first line, and heading. A question is ranked two ways:

- BM25 keyword scoring with `k1 = 1.2` and `b = 0.75`, so a rare word like `rollback` counts for more than a common word like `deploy`.
- Cosine similarity on a 64-dimension hashed embedding, a stand-in for a real embedding model that needs no download.

Hybrid mode fuses the two rankings with reciprocal rank fusion (`1 / (60 + rank)` summed across lists). Only passages with a positive score enter each list, so a passage with no matching keywords is not promoted just for being listed. The answer is the top passage with a citation such as `rollback.md:3`. If the top passage has no BM25 score, or covers less than 30% of the question's terms, the question is refused. No hosted model is called.

```bash
pip install -r requirements.txt
pytest -q
PYTHONPATH=src uvicorn hybrid.main:app --reload
```

| Method and path | Returns |
| --- | --- |
| `POST /ask` | `question`, optional `mode` (`hybrid`, `bm25`, `dense`), `top_k` (1 to 10), and `source` |
| `GET /sources` | Each corpus file and its passage count |

Each passage in the response carries `bm25`, `dense`, `fused`, `bm25_rank`, `dense_rank`, and `coverage`, so you can see why it ranked where it did.

```bash
curl -s -X POST localhost:8000/ask -H 'content-type: application/json' \
  -d '{"question":"Who may roll back without approval?","mode":"hybrid","top_k":3}'
```
