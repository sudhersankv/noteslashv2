from app.services.chunking import chunk_transcript, SPEAKER_PATTERN


def test_speaker_pattern_matches():
    text = "Interviewer: Hello\nParticipant: Hi there"
    assert SPEAKER_PATTERN.search(text)


def test_chunk_by_speaker():
    text = """Interviewer: How was setup?
Participant: The setup took me almost two days. I was confused.

Interviewer: Anything else?
Participant: Documentation was missing."""
    chunks = chunk_transcript(text)
    assert len(chunks) >= 2
    assert any("two days" in c.text for c in chunks)


def test_empty_returns_empty():
    assert chunk_transcript("   ") == []
