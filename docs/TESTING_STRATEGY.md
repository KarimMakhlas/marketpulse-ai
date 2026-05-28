# Testing Strategy

## Current state (v0.1)

- **34 unit tests** in `tests/`, running in ~1.3s
- **Coverage:** pure functions + orchestrators with injected dependencies
- **No integration tests** — all external boundaries (HTTP, ChromaDB, Gemini) are mocked

## Test pyramid

```
         [  ]        Manual / exploratory (run `make ui`)
        [    ]       Integration (deferred to v0.2)
      [        ]     Unit (34 tests — current focus)
```

## Unit test scope

| Module | What's tested |
|--------|-------------|
| `ingestion/sources.py` | RSS parsing, dedup by content hash, chunking logic |
| `ingestion/indexer.py` | Embedding pipeline with mocked embedder |
| `retrieval/retriever.py` | Score formula, recency weighting, top-k selection |
| `synthesis/prompts.py` | Prompt construction with mock chunks |
| `synthesis/answer.py` | Orchestration with fake `LLMProvider` |
| `llm/gemini.py` | Provider interface compliance |

## Rules (see `.claude/rules/testing.md` for full detail)

- No network calls in tests
- No real LLM calls — inject `FakeLLMProvider`
- No real ChromaDB — mock `Collection`
- Test files mirror source: `tests/test_<module>.py`

## Running tests

```bash
make test                          # all tests
uv run pytest tests/test_foo.py -v # one file
uv run pytest -k "chunk" -v        # by keyword
```

## v0.2 plan

- Add integration tests against a test ChromaDB instance
- Add regression tests for the retrieval scoring formula
- Consider RAGAS for RAG-specific evaluation (deferred until v0.3)
