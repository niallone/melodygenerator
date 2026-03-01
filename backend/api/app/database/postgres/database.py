from .PostgresDatabase import PostgresDatabase


class DatabaseManager:
    """
    A singleton manager for database connections.

    This class ensures that only one database connection is created
    and reused throughout the application.
    """

    _instance = None

    @classmethod
    async def get_instance(cls) -> PostgresDatabase:
        """
        Get or create a PostgresDatabase instance.

        This method implements the singleton pattern, ensuring that only
        one database connection is created. If the connection doesn't exist,
        it creates one using environment variables for configuration.

        :return: An instance of PostgresDatabase
        """
        if cls._instance is None:
            # Create a new PostgresDatabase instance using environment variables
            cls._instance = PostgresDatabase.from_env()
            # Initialise the database connection pool
            await cls._instance.initialise()
        return cls._instance


# Create a global instance of DatabaseManager
pg_db = DatabaseManager()
