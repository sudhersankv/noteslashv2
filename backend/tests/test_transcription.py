from app.services.media import is_audio_file


def test_audio_by_extension():
    assert is_audio_file("episode.mp3", None)
    assert is_audio_file("voice.wav", "application/octet-stream")
    assert not is_audio_file("notes.txt", "text/plain")


def test_audio_by_mime():
    assert is_audio_file("file.bin", "audio/mpeg")
