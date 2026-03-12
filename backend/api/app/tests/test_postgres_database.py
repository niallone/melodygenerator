import os
from unittest.mock import patch

import pytest


class TestFromEnvValidation:
    def test_missing_host_raises(self):
        from app.database.postgres.PostgresDatabase import PostgresDatabase

        env = {
            "POSTGRES_USER": "u",
            "POSTGRES_PASSWORD": "p",
            "POSTGRES_DB": "db",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="PG_DB_HOST"):
                PostgresDatabase.from_env()

    def test_missing_multiple_raises(self):
        from app.database.postgres.PostgresDatabase import PostgresDatabase

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="PG_DB_HOST"):
                PostgresDatabase.from_env()

    def test_all_present_succeeds(self):
        from app.database.postgres.PostgresDatabase import PostgresDatabase

        env = {
            "PG_DB_HOST": "localhost",
            "POSTGRES_USER": "u",
            "POSTGRES_PASSWORD": "p",
            "POSTGRES_DB": "db",
        }
        with patch.dict(os.environ, env, clear=True):
            db = PostgresDatabase.from_env()
            assert db.config["host"] == "localhost"
            assert db.config["min_connections"] == 2
            assert db.config["max_connections"] == 10
