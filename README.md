# Hybrid Search RAG

Level: 7 — Intermediate RAG

Skills: Python, keyword overlap, hashed embeddings

Rank a local markdown corpus by the average of keyword overlap and a hashed-embedding cosine. A question with no shared terms is refused. No hosted model is called.

```bash
pip install -r requirements.txt
pytest -q
```
