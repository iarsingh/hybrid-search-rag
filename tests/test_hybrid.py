from fastapi.testclient import TestClient

from hybrid.main import app
from hybrid.search import bm25_scores, chunk, rrf

client = TestClient(app)


def ask(question, **extra):
    return client.post("/ask", json={"question": question, **extra})


def test_fuses_keyword_and_refuses_an_unrelated_question():
    hit = ask("Why does the platform refuse production?").json()
    assert hit["answered"] is True
    assert hit["passages"][0]["source"] == "refusals.md"
    miss = ask("orbital mechanics homework").json()
    assert miss["answered"] is False


def test_rare_terms_outweigh_common_ones():
    scores = bm25_scores("deploy rollback", ["deploy deploy deploy", "deploy rollback"])
    assert scores[1] > scores[0]


def test_reciprocal_rank_fusion_rewards_agreement():
    fused = rrf([["a", "b", "c"], ["c", "a", "b"]])
    assert sorted(fused, key=fused.get, reverse=True) == ["a", "c", "b"]


def test_markdown_is_chunked_by_paragraph_with_line_numbers():
    chunks = chunk("x.md", "# Title\n\nFirst para\ncontinues.\n\nSecond para.\n")
    assert [(c["line"], c["heading"], c["text"]) for c in chunks] == [
        (3, "Title", "First para continues."),
        (6, "Title", "Second para."),
    ]


def test_answer_cites_file_and_line():
    hit = ask("Who may roll back without approval?").json()
    assert hit["answered"] is True
    assert hit["citation"] == "rollback.md:3"


def test_each_passage_reports_both_ranks():
    passage = ask("error budget minutes").json()["passages"][0]
    assert passage["source"] == "budget.md"
    assert passage["bm25_rank"] == 1
    assert {"dense_rank", "fused", "coverage"} <= set(passage)


def test_modes_and_source_filter():
    assert ask("error budget", mode="bm25").json()["mode"] == "bm25"
    only = ask("engineer page", source="oncall.md", top_k=5).json()["passages"]
    assert {p["source"] for p in only} == {"oncall.md"}
    assert ask("error budget", mode="magic").status_code == 422
    assert ask("error budget", source="missing.md").status_code == 422


def test_question_and_top_k_are_validated():
    assert ask("   ").status_code == 422
    assert ask("error budget", top_k=11).status_code == 422
    assert len(ask("engineer", top_k=2).json()["passages"]) == 2


def test_sources_lists_passage_counts():
    sources = {s["name"]: s["passages"] for s in client.get("/sources").json()["sources"]}
    assert sources["oncall.md"] == 2
    assert sources["budget.md"] == 1
