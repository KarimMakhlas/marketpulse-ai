"""Streamlit UI — single-page MarketPulse demo.

Launch with `make ui` (which runs `uv run streamlit run src/marketpulse/ui/app.py`).
"""

from __future__ import annotations

# Load .env before importing anything that reads GEMINI_API_KEY.
from dotenv import load_dotenv

load_dotenv()

import streamlit as st  # noqa: E402

from marketpulse.db import ensure_schema  # noqa: E402
from marketpulse.llm.gemini import GeminiProvider  # noqa: E402
from marketpulse.synthesis.answer import Citation, answer  # noqa: E402

ensure_schema()

EXAMPLE_QUERIES = [
    "What did the financial press report this week about the Federal Reserve?",
    "What's happening with AI chip stocks?",
    "Any major news about European markets?",
]


@st.cache_resource
def _provider() -> GeminiProvider:
    """Cached across reruns so the Gemini client isn't rebuilt on every keystroke."""
    return GeminiProvider()


def _render_sources(citations: list[Citation]) -> None:
    st.subheader("Sources")
    for c in citations:
        date = c.published_at.strftime("%Y-%m-%d %H:%M")
        st.markdown(f"**{c.marker}** {c.source} · {date}  \n[{c.title}]({c.url})")
        with st.expander("how it ranked"):
            cols = st.columns(3)
            cols[0].metric("similarity", f"{c.similarity:.3f}")
            cols[1].metric("recency", f"{c.recency:.3f}")
            cols[2].metric("score", f"{c.score:.3f}")


def main() -> None:
    st.set_page_config(page_title="MarketPulse AI", page_icon="📈", layout="centered")

    st.title("📈 MarketPulse AI")
    st.caption(
        "Ask questions about today's financial news. "
        "Indexed from FT, MarketWatch, Yahoo Finance, CNBC, Guardian & SEC EDGAR; "
        "answered by Gemini with Self-RAG relevance gating."
    )

    with st.form("query_form", clear_on_submit=False):
        query = st.text_input(
            "Your question",
            placeholder=EXAMPLE_QUERIES[0],
            label_visibility="collapsed",
        )
        col_btn, col_k = st.columns([1, 1])
        submitted = col_btn.form_submit_button("Ask", type="primary", use_container_width=True)
        k = col_k.slider("k (sources)", min_value=1, max_value=10, value=5)

    if not submitted:
        st.divider()
        st.markdown("**Try one of these:**")
        for q in EXAMPLE_QUERIES:
            st.markdown(f"- {q}")
        return

    if not query.strip():
        st.warning("Please enter a question.")
        return

    try:
        provider = _provider()
    except RuntimeError as e:
        st.error(str(e))
        return

    with st.spinner("Checking source relevance…"):
        try:
            result = answer(query, provider=provider, k=k)
        except Exception as exc:
            msg = str(exc)
            if "503" in msg or "UNAVAILABLE" in msg:
                st.warning(
                    "Gemini is temporarily overloaded (503). "
                    "Wait a few seconds and try again."
                )
            else:
                st.error(f"Unexpected error: {exc}")
            return

    # Refusal path — Self-RAG grader found no relevant sources.
    if result.refused:
        st.warning("".join(result.tokens))
        st.info(
            "The Self-RAG grader determined the indexed sources don't cover this question. "
            "Try `make ingest` to refresh, or ask something more directly covered by recent news."
        )
        if result.citations:
            with st.expander("Retrieved (but insufficient) sources"):
                _render_sources(result.citations)
        return

    # Empty-index path.
    if not result.citations:
        st.warning("".join(result.tokens))
        st.info("Run `make ingest` from your terminal to populate the index, then retry.")
        return

    # Relevance badge.
    if result.doc_grade == "sufficient":
        st.success("Sources graded: relevant", icon="✓")

    st.subheader("Answer")
    answer_slot = st.empty()
    full_answer = ""
    try:
        for token in result.tokens:
            full_answer += token
            answer_slot.markdown(full_answer + "▌")
        answer_slot.markdown(full_answer)
    except Exception as e:  # noqa: BLE001
        st.error(f"Streaming failed: {e}")
        if full_answer:
            answer_slot.markdown(full_answer)

    _render_sources(result.citations)


main()
