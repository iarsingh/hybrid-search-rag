# Hybrid Search RAG

<!-- project-guide:start -->
## Project guide

[Project architecture](PROJECT_ARCHITECTURE.md) · [Interview questions and answers](INTERVIEW_QA.md)

Use the architecture document for the component diagram, implementation boundaries, and verification entry points. The interview guide includes source-backed answers and project walkthroughs.

### Implementation map

| Component | Responsibility |
| --- | --- |
| [`src/hybrid/main.py`](src/hybrid/main.py) | HTTP handlers: `GET /healthz`, `GET /sources`, `POST /ask` |
| [`src/hybrid/search.py`](src/hybrid/search.py) | Functions: `stem`, `tokens`, `embed`, `chunk`, `load_corpus`, `bm25_scores`, `rrf` |
| [`requirements.txt`](requirements.txt) | Implementation or supporting configuration |
| [`src/hybrid/__init__.py`](src/hybrid/__init__.py) | Implementation or supporting configuration |
| [`tests/test_hybrid.py`](tests/test_hybrid.py) | Executable checks and regression examples |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | GitHub Actions job definitions |
| [`README.md`](README.md) | Project explanations or operating notes |
| [`corpus/budget.md`](corpus/budget.md) | Project explanations or operating notes |
| [`corpus/oncall.md`](corpus/oncall.md) | Project explanations or operating notes |

### Local setup and verification

From the repository root (the commands follow the checked-in manifests):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

To serve the FastAPI application locally, install the server separately if it is not already available:

```bash
python -m pip install uvicorn
PYTHONPATH=src python -m uvicorn hybrid.main:app --reload
```

<!-- project-guide:end -->

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

## Ops plane

Workspaces, tenant isolation, job approval, and audit live under `/v1`. Production apply is refused. See `docs/ARCHITECTURE.md`.
