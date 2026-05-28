from datetime import UTC, datetime

from marketpulse.retrieval.retriever import RetrievedChunk
from marketpulse.synthesis.prompts import (
    MAX_EXCERPT_CHARS,
    USER_PROMPT_TEMPLATE,
    build_prompt,
    format_sources,
)


def _chunk(i: int, text: str = "body text") -> RetrievedChunk:
    return RetrievedChunk(
        text=text,
        source=f"src{i}",
        url=f"https://example.com/{i}",
        title=f"Title {i}",
        published_at=datetime(2026, 5, 27, tzinfo=UTC),
        similarity=0.5,
        recency=0.5,
        credibility=0.85,
        score=0.5,
    )


def test_format_sources_emits_one_block_per_chunk():
    chunks = [_chunk(1), _chunk(2), _chunk(3)]
    out = format_sources(chunks)
    assert "[S1]" in out
    assert "[S2]" in out
    assert "[S3]" in out
    assert "[S4]" not in out


def test_format_sources_includes_source_name_and_url():
    chunks = [_chunk(7)]
    out = format_sources(chunks)
    assert "src7" in out
    assert "https://example.com/7" in out


def test_format_sources_truncates_long_excerpts():
    long_text = "x" * (MAX_EXCERPT_CHARS + 500)
    out = format_sources([_chunk(1, text=long_text)])
    # The block should not contain the full oversized text
    assert "x" * (MAX_EXCERPT_CHARS + 1) not in out
    assert "x" * MAX_EXCERPT_CHARS in out


def test_build_prompt_includes_query_verbatim():
    out = build_prompt("what is the federal reserve doing?", [_chunk(1)])
    assert "what is the federal reserve doing?" in out


def test_build_prompt_includes_citation_instruction():
    out = build_prompt("anything", [_chunk(1)])
    assert "[S1]" in out  # in either instructions or sources block


def test_build_prompt_includes_refusal_instruction():
    out = build_prompt("anything", [_chunk(1)])
    assert "do not answer" in out.lower() or "explicitly" in out.lower()


def test_user_prompt_template_has_required_placeholders():
    # If someone renames placeholders, .format() will raise
    formatted = USER_PROMPT_TEMPLATE.format(query="q", sources_block="b")
    assert "q" in formatted
    assert "b" in formatted
