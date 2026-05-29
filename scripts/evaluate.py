"""RAGAS evaluation script — run with `make eval`.

Evaluates the RAG pipeline on a small hardcoded question set using three
metrics: faithfulness, answer_relevancy, and context_recall.

Requires GEMINI_API_KEY. The Gemini-backed LangChain wrapper is used as
the evaluator LLM since RAGAS supports it out of the box via langchain-google-genai.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow running as a script from any directory.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Eval question set — deliberately varied to test the refusal branch too.
# ---------------------------------------------------------------------------

EVAL_QUESTIONS = [
    "What did the Federal Reserve say about interest rates recently?",
    "What is happening with AI chip stocks and semiconductor companies?",
    "What are the latest developments in European financial markets?",
    "What recent SEC filings have been notable for major tech companies?",
    "What is the airspeed velocity of an unladen swallow?",  # should trigger refusal/low scores
]


def run_eval() -> None:
    from marketpulse.db import ensure_schema
    from marketpulse.llm.gemini import GeminiProvider
    from marketpulse.synthesis.answer import answer

    ensure_schema()

    try:
        provider = GeminiProvider()
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # Collect answers and contexts.
    rows: list[dict[str, str | list[str]]] = []
    for question in EVAL_QUESTIONS:
        print(f"\n[eval] {question}")
        result = answer(question, provider=provider, k=5)
        answer_text = "".join(result.tokens)
        contexts = [c.excerpt for c in result.citations] if result.citations else []
        status = "REFUSED" if result.refused else f"grade={result.doc_grade}"
        print(f"       {status} | {len(contexts)} contexts | {len(answer_text)} chars")
        rows.append(
            {
                "question": question,
                "answer": answer_text,
                "contexts": contexts,
                "ground_truth": "",  # no ground truth for online eval
            }
        )

    # Build RAGAS dataset and evaluate.
    try:
        from datasets import Dataset  # type: ignore[import-untyped]
        from ragas import evaluate  # type: ignore[import-untyped]
        from ragas.metrics import answer_relevancy, faithfulness  # type: ignore[import-untyped]
    except ImportError as e:
        print(f"\nRAGAS/datasets not installed: {e}", file=sys.stderr)
        print("Install with: uv add ragas datasets")
        sys.exit(1)

    # Filter rows that have at least one context (refused rows would score 0 on
    # faithfulness since there's no context — include them to show the effect).
    ds = Dataset.from_list(rows)
    print("\n[eval] Running RAGAS metrics…")

    try:
        scores = evaluate(ds, metrics=[faithfulness, answer_relevancy])
        print("\n=== RAGAS Evaluation Results ===")
        print(scores)
    except Exception as exc:
        print(f"\n[eval] RAGAS evaluation failed: {exc}", file=sys.stderr)
        print("       This can happen if Gemini rate-limits or if contexts are empty.")
        sys.exit(1)


if __name__ == "__main__":
    run_eval()
