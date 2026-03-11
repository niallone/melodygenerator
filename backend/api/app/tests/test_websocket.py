"""Tests for the WebSocket melody generation endpoint."""

from starlette.testclient import TestClient


def test_websocket_missing_model(app_with_mock_db):
    """WebSocket returns error when model_id is not found."""
    app_with_mock_db.state.models = {}
    client = TestClient(app_with_mock_db)

    with client.websocket_connect("/melody/generate/stream") as ws:
        ws.send_json({"type": "start_generation", "model_id": "nonexistent"})
        response = ws.receive_json()

    assert response["type"] == "error"
    assert "not found" in response["message"].lower()


def test_websocket_missing_start_message(app_with_mock_db):
    """WebSocket returns error when first message is not start_generation."""
    client = TestClient(app_with_mock_db)

    with client.websocket_connect("/melody/generate/stream") as ws:
        ws.send_json({"type": "wrong_type"})
        response = ws.receive_json()

    assert response["type"] == "error"
    assert "start_generation" in response["message"]


def test_websocket_no_model_id(app_with_mock_db):
    """WebSocket returns error when model_id is missing."""
    client = TestClient(app_with_mock_db)

    with client.websocket_connect("/melody/generate/stream") as ws:
        ws.send_json({"type": "start_generation"})
        response = ws.receive_json()

    assert response["type"] == "error"
    assert "model_id" in response["message"].lower()


def test_websocket_invalid_params(app_with_mock_db, mock_models):
    """WebSocket returns error for out-of-range parameters."""
    app_with_mock_db.state.models = mock_models
    client = TestClient(app_with_mock_db)

    with client.websocket_connect("/melody/generate/stream") as ws:
        ws.send_json(
            {
                "type": "start_generation",
                "model_id": "test_model",
                "temperature": 99.0,
                "num_notes": -1,
            }
        )
        response = ws.receive_json()

    assert response["type"] == "error"
    assert "temperature" in response["message"]
    assert "num_notes" in response["message"]
