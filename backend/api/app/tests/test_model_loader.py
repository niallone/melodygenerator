"""Tests for ModelBundle and model loader utilities."""

from unittest.mock import MagicMock

from app.src.services.model_loader import ModelBundle


class TestModelBundleArchitecture:
    def test_transformer_architecture(self):
        model = MagicMock()
        model.d_model = 256
        bundle = ModelBundle(
            model=model,
            seeds=None,
            pitchnames=None,
            note_to_int=None,
            n_vocab=100,
            model_version=1,
            tokenizer=None,
        )
        assert bundle.architecture == "transformer"

    def test_lstm_architecture(self):
        model = MagicMock(spec=[])
        bundle = ModelBundle(
            model=model,
            seeds=None,
            pitchnames=None,
            note_to_int=None,
            n_vocab=100,
            model_version=1,
            tokenizer=None,
        )
        assert bundle.architecture == "lstm"

    def test_bundle_stores_fields(self):
        model = MagicMock(spec=[])
        bundle = ModelBundle(
            model=model,
            seeds=[[1, 2]],
            pitchnames=["C4"],
            note_to_int={"C4": 0},
            n_vocab=50,
            model_version=3,
            tokenizer=None,
        )
        assert bundle.n_vocab == 50
        assert bundle.model_version == 3
        assert bundle.seeds == [[1, 2]]
        assert bundle.pitchnames == ["C4"]
        assert bundle.note_to_int == {"C4": 0}
