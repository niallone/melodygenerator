import asyncio
import json
import logging
import os
import re
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, List, Optional

import asyncpg
from asyncpg import Connection, Pool

# Pattern for validating SQL identifiers (table/column names)
_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def _validate_identifier(name: str) -> str:
    """Validate a SQL identifier to prevent injection."""
    if not _IDENTIFIER_PATTERN.match(name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return name


class PostgresDatabase:
    """A class to manage PostgreSQL database connections and operations."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.pool: Optional[Pool] = None
        self.logger = logging.getLogger(__name__)
        self.retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 1)
        self._init_lock = asyncio.Lock()

    @classmethod
    def from_env(cls):
        """Create a PostgresDatabase instance from environment variables."""
        config = {
            "host": os.getenv("PG_DB_HOST"),
            "port": int(os.getenv("PG_DB_PORT", "5432")),
            "user": os.getenv("POSTGRES_USER"),
            "password": os.getenv("POSTGRES_PASSWORD"),
            "database": os.getenv("POSTGRES_DB"),
            "min_connections": int(os.getenv("PG_DB_MIN_CONNECTIONS", "10")),
            "max_connections": int(os.getenv("PG_DB_MAX_CONNECTIONS", "100")),
            "command_timeout": int(os.getenv("PG_DB_COMMAND_TIMEOUT", "60")),
            "max_inactive_connection_lifetime": int(os.getenv("PG_DB_MAX_INACTIVE_CONNECTION_LIFETIME", "300")),
        }
        return cls(config)

    async def initialise(self):
        """Initialise the database connection pool."""
        async with self._init_lock:
            if self.pool and not self.pool._closed:
                return
            try:
                pool_config = {
                    "host": self.config["host"],
                    "port": self.config["port"],
                    "user": self.config["user"],
                    "password": self.config["password"],
                    "database": self.config["database"],
                    "min_size": self.config.get("min_connections", 10),
                    "max_size": self.config.get("max_connections", 100),
                    "command_timeout": self.config.get("command_timeout", 60),
                    "max_inactive_connection_lifetime": self.config.get("max_inactive_connection_lifetime", 300),
                    "connection_class": asyncpg.connection.Connection,
                    "init": self.setup_connection,
                }
                self.pool = await asyncpg.create_pool(**pool_config)
                self.logger.info("Database pool initialised successfully.")
            except Exception as e:
                self.logger.error(f"Failed to initialise database pool: {str(e)}")
                raise

    @staticmethod
    async def setup_connection(conn: Connection):
        """Set up a new database connection with custom codecs."""
        await conn.set_type_codec(
            "json",
            encoder=lambda value: json.dumps(value) if value is not None else None,
            decoder=lambda value: json.loads(value) if value is not None else None,
            schema="pg_catalog",
            format="text",
        )
        await conn.set_type_codec(
            "jsonb",
            encoder=lambda value: json.dumps(value) if value is not None else None,
            decoder=lambda value: json.loads(value) if value is not None else None,
            schema="pg_catalog",
            format="text",
        )

    def retry_operation(max_retries: int = 3, retry_delay: float = 1.0):
        """Decorator for retrying database operations on connection failures."""

        def decorator(func):
            @wraps(func)
            async def wrapper(self, *args, **kwargs):
                for attempt in range(max_retries):
                    try:
                        return await func(self, *args, **kwargs)
                    except (asyncpg.exceptions.ConnectionDoesNotExistError, asyncpg.exceptions.InterfaceError) as e:
                        if attempt == max_retries - 1:
                            self.logger.error(f"Operation failed after {max_retries} attempts: {str(e)}")
                            raise
                        self.logger.warning(
                            f"Operation failed, retrying (attempt {attempt + 1}/{max_retries}): {str(e)}"
                        )
                        await asyncio.sleep(retry_delay)
                        if self.pool.is_closed():
                            await self.initialise()

            return wrapper

        return decorator

    @asynccontextmanager
    async def transaction(self):
        """Context manager for database transactions."""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn

    @retry_operation()
    async def execute(self, query: str, *args, timeout: Optional[float] = None) -> str:
        """Execute a SQL query."""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args, timeout=timeout)

    @retry_operation()
    async def fetch(self, query: str, *args, timeout: Optional[float] = None) -> List[asyncpg.Record]:
        """Fetch multiple rows from a SQL query."""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args, timeout=timeout)

    @retry_operation()
    async def fetchrow(self, query: str, *args, timeout: Optional[float] = None) -> Optional[asyncpg.Record]:
        """Fetch a single row from a SQL query."""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args, timeout=timeout)

    @retry_operation()
    async def fetchval(self, query: str, *args, column: int = 0, timeout: Optional[float] = None) -> Any:
        """Fetch a single value from a SQL query."""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args, column=column, timeout=timeout)

    async def batch_insert(self, table: str, columns: List[str], values: List[List[Any]], chunk_size: int = 1000):
        """Perform a batch insert operation with validated identifiers."""
        safe_table = _validate_identifier(table)
        safe_columns = [_validate_identifier(c) for c in columns]
        query = f"INSERT INTO {safe_table} ({', '.join(safe_columns)}) VALUES "
        async with self.transaction() as conn:
            for i in range(0, len(values), chunk_size):
                chunk = values[i : i + chunk_size]
                ncols = len(safe_columns)
                value_placeholders = [
                    f"({', '.join('$' + str(j) for j in range(idx * ncols + 1, (idx + 1) * ncols + 1))})"
                    for idx in range(len(chunk))
                ]
                chunk_query = query + ", ".join(value_placeholders)
                flattened_values = [item for sublist in chunk for item in sublist]
                await conn.execute(chunk_query, *flattened_values)

    @retry_operation()
    async def execute_many(self, query: str, args_list: List[List[Any]]):
        """Execute a query with multiple sets of parameters."""
        async with self.transaction() as conn:
            await conn.executemany(query, args_list)

    async def close(self):
        """Close the database pool."""
        if self.pool:
            await self.pool.close()
            self.logger.info("Database pool closed.")
