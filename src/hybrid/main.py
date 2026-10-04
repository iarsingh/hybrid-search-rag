from fastapi import FastAPI, HTTPException

from hybrid.search import SearchError, load_corpus, search

app = FastAPI()


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/sources")
def sources():
    counts = {}
    for passage in load_corpus():
        counts[passage["source"]] = counts.get(passage["source"], 0) + 1
    return {"sources": [{"name": name, "passages": count} for name, count in sorted(counts.items())]}


@app.post("/ask")
def post_ask(body: dict):
    try:
        return search(body.get("question"), body.get("mode", "hybrid"), body.get("top_k", 3), body.get("source"))
    except SearchError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
