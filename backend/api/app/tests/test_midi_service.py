from unittest.mock import MagicMock

from app.src.services.midi_service import token_to_note_event


class TestTokenToNoteEvent:
    def test_returns_none_for_no_tokenizer(self):
        assert token_to_note_event(0, None, 0, 0.0) is None

    def test_returns_note_for_pitch_token(self):
        tokenizer = MagicMock()
        tokenizer.vocab = ["Pitch_60", "Pitch_72", "Duration_0.5"]

        result = token_to_note_event(0, tokenizer, 5, 2.0)
        assert result is not None
        assert result["type"] == "note"
        assert result["pitch"] == 60
        assert result["index"] == 5
        assert result["offset"] == 2.0

    def test_returns_none_for_non_pitch_token(self):
        tokenizer = MagicMock()
        tokenizer.vocab = ["Duration_0.5", "Velocity_80"]

        result = token_to_note_event(0, tokenizer, 0, 0.0)
        assert result is None

    def test_returns_none_for_out_of_range_token(self):
        tokenizer = MagicMock()
        tokenizer.vocab = ["Pitch_60"]

        result = token_to_note_event(999, tokenizer, 0, 0.0)
        assert result is None
