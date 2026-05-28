"""Streamlit UI — single-page MarketPulse demo.

Launch with `make ui` (which runs `uv run streamlit run src/marketpulse/ui/app.py`).
"""

from __future__ import annotations

# Load .env before importing anything that reads GEMINI_API_KEY.
from dotenv import load_dotenv

load_dotenv()

import streamlit as st  # noqa: E402

from marketpulse.llm.gemini import GeminiProvider  # noqa: E402
from marketpulse.synthesis.answer import Citation, answer  # noqa: E402

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
        "Ask questions about today's financial news. Indexed from FT + MarketWatch RSS feeds; "
        "answered by Gemini with inline citations."
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

    # Provider construction surfaces missing-key errors as a friendly message.
    try:
        provider = _provider()
    except RuntimeError as e:
        st.error(str(e))
        return

    with st.spinner("Retrieving relevant chunks…"):
        result = answer(query, provider=provider, k=k)

    # Empty-index path: the synthetic stream carries the explanatory message.
    if not result.citations:
        st.warning("".join(result.tokens))
        st.info("Run `make ingest` from your terminal to populate the index, then retry.")
        return

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
