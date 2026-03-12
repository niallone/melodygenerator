class TestCorsOrigins:
    def test_single_origin(self):
        from app.src.config import Settings

        s = Settings(allowed_origins="https://example.com", debug=False)
        assert s.cors_origins == ["https://example.com"]

    def test_multiple_origins(self):
        from app.src.config import Settings

        s = Settings(allowed_origins="https://a.com, https://b.com", debug=False)
        assert s.cors_origins == ["https://a.com", "https://b.com"]

    def test_empty_string(self):
        from app.src.config import Settings

        s = Settings(allowed_origins="", debug=False)
        assert s.cors_origins == []

    def test_debug_adds_localhost(self):
        from app.src.config import Settings

        s = Settings(allowed_origins="https://example.com", debug=True)
        assert "http://localhost:3000" in s.cors_origins

    def test_debug_no_duplicate_localhost(self):
        from app.src.config import Settings

        s = Settings(allowed_origins="http://localhost:3000", debug=True)
        assert s.cors_origins.count("http://localhost:3000") == 1


class TestR2Enabled:
    def test_enabled_when_all_set(self):
        from app.src.config import Settings

        s = Settings(
            r2_endpoint_url="https://r2.example.com",
            r2_access_key_id="key",
            r2_secret_access_key="secret",
            r2_bucket_name="bucket",
        )
        assert s.r2_enabled is True

    def test_disabled_when_missing_endpoint(self):
        from app.src.config import Settings

        s = Settings(r2_access_key_id="key", r2_bucket_name="bucket")
        assert s.r2_enabled is False

    def test_disabled_when_missing_key(self):
        from app.src.config import Settings

        s = Settings(r2_endpoint_url="https://r2.example.com", r2_bucket_name="bucket")
        assert s.r2_enabled is False

    def test_disabled_by_default(self):
        from app.src.config import Settings

        s = Settings()
        assert s.r2_enabled is False
