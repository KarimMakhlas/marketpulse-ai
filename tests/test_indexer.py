import pytest

from marketpulse.ingestion.indexer import chunk_text


def test_chunk_text_empty_string_returns_empty_list():
    assert chunk_text("") == []


def test_chunk_text_whitespace_only_returns_empty_list():
    assert chunk_text("   \n\t  ") == []


def test_chunk_text_short_input_returns_single_chunk():
    text = "short text under chunk size"
    assert chunk_text(text, chunk_size=100, overlap=10) == [text]


def test_chunk_text_long_input_produces_multiple_chunks():
    text = "a" * 1000
    chunks = chunk_text(text, chunk_size=400, overlap=50)
    assert len(chunks) > 1
    # each chunk respects max size
    assert all(len(c) <= 400 for c in chunks)


def test_chunk_text_chunks_overlap_correctly():
    # 1000 chars, chunk=400, overlap=50 → step=350
    # chunk[0] = chars[0..400], chunk[1] = chars[350..750]
    # last 50 chars of chunk[0] == first 50 chars of chunk[1]
    text = "".join(f"{i % 10}" for i in range(1000))
    chunks = chunk_text(text, chunk_size=400, overlap=50)
    assert chunks[0][-50:] == chunks[1][:50]


def test_chunk_text_covers_full_input():
    text = "a" * 1000
    chunks = chunk_text(text, chunk_size=400, overlap=50)
    # reconstruct unique characters covered
    reconstructed = chunks[0]
    for next_chunk in chunks[1:]:
        # each subsequent chunk starts 350 chars in
        reconstructed += next_chunk[50:]
    # may exceed the input length due to last-chunk padding, but must cover it
    assert reconstructed.startswith(text) or len(reconstructed) >= len(text)


def test_chunk_text_rejects_overlap_ge_chunk_size():
    with pytest.raises(ValueError):
        chunk_text("some text here", chunk_size=100, overlap=100)
