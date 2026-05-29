"""CLI: `python -m marketpulse.synthesis "your question" [--k 5]`.

Loads `.env` before any other project import so GeminiProvider sees the key.
"""

from __future__ import annotations

# dotenv must run before any code that reads os.environ["GEMINI_API_KEY"].
from dotenv import load_dotenv

load_dotenv()

import argparse  # noqa: E402
import logging  # noqa: E402
import sys  # noqa: E402

from ..llm.gemini import GeminiProvider  # noqa: E402
from ..retrieval.retriever import DEFAULT_K  # noqa: E402
from .answer import answer  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(prog="marketpulse.synthesis")
    parser.add_argument("query", help="Natural-language question")
    parser.add_argument("--k", type=int, default=DEFAULT_K, help=f"top-k (default {DEFAULT_K})")
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(message)s")

    try:
        provider = GeminiProvider()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    result = answer(args.query, provider=provider, k=args.k)

    if not result.citations:
        # Empty-index path: tokens carry the explanatory message.
        for token in result.tokens:
            sys.stdout.write(token)
        sys.stdout.write("\n")
        return 0

    print("Sources:")
    for c in result.citations:
        date = c.published_at.strftime("%Y-%m-%d")
        print(f"  {c.marker}  {c.source} ({date})  {c.title}")
        print(f"        {c.url}")
    print()
    # Self-RAG grader refused — distinguish from a real answer so the reader
    # doesn't mistake the refusal text for a grounded response.
    header = "Refused (insufficient sources):" if result.refused else "Answer:"
    print(header)
    try:
        for token in result.tokens:
            sys.stdout.write(token)
            sys.stdout.flush()
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
            print(
                "\nGemini free-tier quota exhausted (429). "
                "The gemini-flash-latest alias currently routes to a model with a "
                "20 req/day free-tier limit. Wait for daily reset or set a paid key.",
                file=sys.stderr,
            )
            return 2
        if "503" in msg or "UNAVAILABLE" in msg:
            print(
                "\nGemini is temporarily overloaded (503). Try again in a few seconds.",
                file=sys.stderr,
            )
            return 2
        print(f"\nerror during streaming: {e}", file=sys.stderr)
        return 1
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
