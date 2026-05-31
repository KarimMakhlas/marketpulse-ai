from conftest import make_chunk
from marketpulse.synthesis.answer import (
    MAX_EXCERPT_CHARS,
    USER_PROMPT_TEMPLATE,
    build_prompt,
    format_sources,
)


def test_format_sources_emits_one_block_per_chunk() -> None:
    chunks = [make_chunk(1), make_chunk(2), make_chunk(3)]
    out = format_sources(chunks)
    assert "[S1]" in out
    assert "[S2]" in out
    assert "[S3]" in out
    assert "[S4]" not in out


def test_format_sources_includes_source_name_and_url() -> None:
    chunks = [make_chunk(7, source="reuters")]
    out = format_sources(chunks)
    assert "reuters" in out
    assert "https://example.com/7" in out


def test_format_sources_truncates_long_excerpts() -> None:
    long_text = "x" * (MAX_EXCERPT_CHARS + 500)
    out = format_sources([make_chunk(1, text=long_text)])
    assert "x" * (MAX_EXCERPT_CHARS + 1) not in out
    assert "x" * MAX_EXCERPT_CHARS in out


def test_build_prompt_includes_query_verbatim() -> None:
    out = build_prompt("what is the federal reserve doing?", [make_chunk(1)])
    assert "what is the federal reserve doing?" in out


def test_build_prompt_includes_citation_instruction() -> None:
    out = build_prompt("anything", [make_chunk(1)])
    assert "[S1]" in out


def test_build_prompt_includes_refusal_instruction() -> None:
    out = build_prompt("anything", [make_chunk(1)])
    assert "do not answer" in out.lower() or "explicitly" in out.lower()


def test_user_prompt_template_has_required_placeholders() -> None:
    formatted = USER_PROMPT_TEMPLATE.format(query="q", sources_block="b")
    assert "q" in formatted
    assert "b" in formatted
