from fastapi.testclient import TestClient
from hybrid.main import app

def test_fuses_keyword_and_refuses_an_unrelated_question():
    client = TestClient(app)
    hit = client.post("/ask", json={"question": "Why does the platform refuse production?"}).json()
    assert hit["answered"] is True
    assert hit["passages"][0]["source"] == "refusals.md"
    miss = client.post("/ask", json={"question": "orbital mechanics homework"}).json()
    assert miss["answered"] is False
