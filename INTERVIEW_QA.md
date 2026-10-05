# hybrid-search-rag — interview questions and answers

[README](README.md) · [Project architecture](PROJECT_ARCHITECTURE.md)

Answers below use this repository’s files and implementation. They distinguish existing behavior from suggested extensions; source links let you verify each walkthrough.

## 1. What problem does hybrid-search-rag address, and what can you demonstrate?

Markdown files in `corpus/` are split into paragraphs, each tagged with its file, first line, and heading. A question is ranked two ways:

I would demonstrate the linked implementation or examples and distinguish that evidence from any planned production features. Start with [`README.md`](README.md).

## 2. How is this repository organized?

- [`src/hybrid/main.py`](src/hybrid/main.py): Implementation or supporting configuration.
- [`src/hybrid/search.py`](src/hybrid/search.py): Implementation or supporting configuration.
- [`requirements.txt`](requirements.txt): Implementation or supporting configuration.
- [`src/hybrid/__init__.py`](src/hybrid/__init__.py): Implementation or supporting configuration.
- [`tests/test_hybrid.py`](tests/test_hybrid.py): Executable checks and regression examples.
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml): GitHub Actions job definitions.
- [`README.md`](README.md): Project explanations or operating notes.
- [`corpus/budget.md`](corpus/budget.md): Project explanations or operating notes.

[PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) contains the component diagram and the implementation walkthrough.

## 3. Can you walk through `search` and explain the decision it makes?

The main walkthrough here is `search(question, mode='hybrid', top_k=3, source=None)` in [`src/hybrid/search.py`](src/hybrid/search.py#L99).

```python
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
```

This is an excerpt; follow the source link for the rest of the branches.

The implementation calls `', '.join`, `SearchError`, `bm25_scores`, `embed`, `enumerate`, `fused.setdefault`, `hits.append`, `isinstance`, `len`. In an interview, trace those calls in execution order using a fixture input.

## 4. What responsibility does `chunk` have?

`chunk(name, text)` is defined in [`src/hybrid/search.py`](src/hybrid/search.py#L37).

Its return expressions include:

- `chunks`

It uses `' '.join`, `buffer.append`, `chunks.append`, `enumerate`, `flush`, `line.strip`, `stripped.lstrip`, `stripped.lstrip('#').strip`. This is the code path I would compare against the caller to explain responsibility boundaries.

## 5. What input validation and failure behavior are implemented?

Explicit failure paths include:

- `HTTPException(status_code=422, detail=str(exc))` in [`src/hybrid/main.py`](src/hybrid/main.py#L26).
- `SearchError('question is empty')` in [`src/hybrid/search.py`](src/hybrid/search.py#L101).
- `SearchError(f"mode must be one of {', '.join(sorted(MODES))}")` in [`src/hybrid/search.py`](src/hybrid/search.py#L103).
- `SearchError('top_k must be from 1 to 10')` in [`src/hybrid/search.py`](src/hybrid/search.py#L105).
- `SearchError(f'unknown source: {source}')` in [`src/hybrid/search.py`](src/hybrid/search.py#L109).

I would test both the condition that reaches each exception and the caller that translates it. An explicit raise does not mean every malformed input or dependency failure is handled.

## 6. Which test would you use to demonstrate correctness?

[`tests/test_hybrid.py`](tests/test_hybrid.py#L13) contains `test_fuses_keyword_and_refuses_an_unrelated_question`:

```python
def test_fuses_keyword_and_refuses_an_unrelated_question():
    hit = ask("Why does the platform refuse production?").json()
    assert hit["answered"] is True
    assert hit["passages"][0]["source"] == "refusals.md"
    miss = ask("orbital mechanics homework").json()
    assert miss["answered"] is False
```

This is a concrete regression example from the repository. Its assertions establish that case; they do not establish behavior for every input or under production load.

## 7. What HTTP interface does the code expose?

- `GET /healthz` → `healthz` in [`src/hybrid/main.py`](src/hybrid/main.py#L9).
- `GET /sources` → `sources` in [`src/hybrid/main.py`](src/hybrid/main.py#L14).
- `POST /ask` → `post_ask` in [`src/hybrid/main.py`](src/hybrid/main.py#L22).

These are literal decorators. Application/router prefixes, authentication, and middleware must be checked in the corresponding setup code.

## 8. Where does state live, and what happens with multiple workers?

Module-level containers include `STOP`, `MODES` in [`src/hybrid/search.py`](src/hybrid/search.py).

These containers belong to a Python process. Inspect which are constant fixtures and which are mutated. Mutable process state needs an explicit shared-storage or synchronization strategy before multiple workers can provide consistent behavior.

## 9. How would another engineer reproduce your walkthrough?

Start from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

These commands follow repository manifests; environment setup and command results still need to be checked on the target machine.

## 10. What does automation verify, and what does it not prove?

Inspect [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for triggers, permissions, and job commands. I would name the checks that those definitions run and show the latest run separately. A workflow definition alone does not establish a successful deployment, security review, or production SLO.

## 11. How would you present this project in a Forward Deployed Engineer interview?

Start with the user and operational problem described in [`README.md`](README.md). Explain one constraint that changes the implementation, show the linked code or example, and walk through a success case and a failure case. Agree on a measurable acceptance criterion before expanding the solution, and leave a handoff with data boundaries and rollback ownership. Any proposed production or business metric should be identified as a target until measured.

## 12. What is the input-to-output contract of `search`?

In [`src/hybrid/search.py`](src/hybrid/search.py#L99), `search(question, mode='hybrid', top_k=3, source=None)` receives the inputs. The function computes these intermediate values:

- `passages = load_corpus()`
- `texts = [p['text'] for p in passages]`
- `keyword = bm25_scores(question, texts)`
- `query = embed(question)`
- `dense = [sum((a * b for a, b in zip(query, embed(text)))) for text in texts]`
- `by_bm25 = sorted(range(len(passages)), key=lambda i: (-keyword[i], i))`
- `by_dense = sorted(range(len(passages)), key=lambda i: (-dense[i], i))`

Its result is defined by:

- `{'answered': True, 'answer': best['text'], 'citation': f"{best['source']}:{best['line']}", 'mode': mode, 'passages': hits}`
- `{'answered': False, 'answer': 'No document shares enough terms.', 'citation': None, 'mode': mode, 'passages': hits}`

## 13. Which decision rules or boundary conditions should an interviewer challenge?

The implementation in [`src/hybrid/search.py`](src/hybrid/search.py#L99) branches on:

- `not isinstance(question, str) or not question.strip()`
- `mode not in MODES`
- `not isinstance(top_k, int) or not 1 <= top_k <= 10`
- `source is not None`
- `mode == 'bm25'`
- `not hits or hits[0]['bm25'] <= 0 or hits[0]['coverage'] < MIN_COVERAGE`
- `source not in {p['source'] for p in passages}`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.
