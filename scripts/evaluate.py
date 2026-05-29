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
        from langchain_community.embeddings import (  # type: ignore[import-untyped]
            HuggingFaceEmbeddings,
        )
        from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore[import-untyped]
        from ragas import evaluate  # type: ignore[import-untyped]
        from ragas.embeddings.base import (  # type: ignore[import-untyped]
            LangchainEmbeddingsWrapper,
        )
        from ragas.llms.base import LangchainLLMWrapper  # type: ignore[import-untyped]
        from ragas.metrics import answer_relevancy, faithfulness  # type: ignore[import-untyped]
        from ragas.run_config import RunConfig  # type: ignore[import-untyped]
    except ImportError as e:
        print(f"\nRAGAS / langchain wrappers not installed: {e}", file=sys.stderr)
        print("Install with: uv sync")
        sys.exit(1)

    # RAGAS defaults to OpenAI for both judge LLM and embeddings, which would
    # require OPENAI_API_KEY. Wire it up with Gemini + the same local embedding
    # model the ingestion pipeline already uses, so eval runs on the same stack.
    # `timeout=120` keeps the wrapper from cutting off slow Gemini calls long
    # before our RunConfig timeout fires below.
    eval_llm = LangchainLLMWrapper(
        ChatGoogleGenerativeAI(
            model="gemini-flash-latest",
            google_api_key=os.environ["GEMINI_API_KEY"],
            timeout=120,
        )
    )
    eval_embeddings = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    )

    # Gemini flash free tier is 10 RPM. RAGAS defaults to 16 parallel workers,
    # which trips the rate limit and surfaces as TimeoutError per job. Cap
    # concurrency hard and give each job a generous wall clock so a single
    # slow call doesn't poison the whole metric.
    run_config = RunConfig(max_workers=2, timeout=300)

    # Refused rows have no contexts and will score 0 on faithfulness — keep them
    # in the dataset so the refusal branch is exercised end-to-end.
    ds = Dataset.from_list(rows)
    print(
        "\n[eval] Running RAGAS metrics (judge=gemini-flash-latest, embeds=BAAI/bge-small-en-v1.5)…"
    )

    try:
        scores = evaluate(
            ds,
            metrics=[faithfulness, answer_relevancy],
            llm=eval_llm,
            embeddings=eval_embeddings,
            run_config=run_config,
        )
        print("\n=== RAGAS Evaluation Results ===")
        print(scores)
    except Exception as exc:
        print(f"\n[eval] RAGAS evaluation failed: {exc}", file=sys.stderr)
        print("       This can happen if Gemini rate-limits or if contexts are empty.")
        sys.exit(1)


if __name__ == "__main__":
    run_eval()
