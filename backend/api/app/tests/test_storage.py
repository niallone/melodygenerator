import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the module-level singleton before each test."""
    from app.src.services import storage as storage_module

    storage_module._instance = None
    yield
    storage_module._instance = None


class TestGetStorage:
    def test_returns_none_when_disabled(self):
        from app.src.services.storage import get_storage

        settings = MagicMock(r2_enabled=False)
        assert get_storage(settings) is None

    @patch("app.src.services.storage.boto3")
    def test_returns_instance_when_enabled(self, mock_boto3):
        from app.src.services.storage import StorageService, get_storage

        settings = MagicMock(
            r2_enabled=True,
            r2_endpoint_url="https://r2.example.com",
            r2_access_key_id="key",
            r2_secret_access_key="secret",
            r2_bucket_name="bucket",
            r2_public_url="https://pub.example.com",
        )
        result = get_storage(settings)
        assert isinstance(result, StorageService)

    @patch("app.src.services.storage.boto3")
    def test_singleton_returns_same_instance(self, mock_boto3):
        from app.src.services.storage import get_storage

        settings = MagicMock(
            r2_enabled=True,
            r2_endpoint_url="https://r2.example.com",
            r2_access_key_id="key",
            r2_secret_access_key="secret",
            r2_bucket_name="bucket",
            r2_public_url="https://pub.example.com",
        )
        first = get_storage(settings)
        second = get_storage(settings)
        assert first is second


class TestStorageService:
    @patch("app.src.services.storage.boto3")
    def test_upload_file(self, mock_boto3):
        from app.src.services.storage import StorageService

        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        svc = StorageService("https://r2.example.com", "key", "secret", "bucket", "https://pub.example.com")

        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
            f.write(b"fake midi")
            tmp_path = f.name

        try:
            url = svc.upload_file(tmp_path, "melodies/test.mid")
            assert url == "https://pub.example.com/melodies/test.mid"
            mock_client.upload_file.assert_called_once()
        finally:
            os.unlink(tmp_path)

    @patch("app.src.services.storage.boto3")
    def test_delete_file(self, mock_boto3):
        from app.src.services.storage import StorageService

        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        svc = StorageService("https://r2.example.com", "key", "secret", "bucket", "https://pub.example.com")
        svc.delete_file("melodies/test.mid")

        mock_client.delete_object.assert_called_once_with(Bucket="bucket", Key="melodies/test.mid")
