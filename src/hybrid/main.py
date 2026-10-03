from fastapi import FastAPI
from hybrid.search import search

app = FastAPI()

@app.post("/ask")
def post_ask(body: dict):
    return search(body["question"])
