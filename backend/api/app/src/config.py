from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(env_file=".env", extra="ignore")

    model_dir: str = "/usr/src/api/app/model"
    output_dir: str = "/usr/src/api/app/output"
    pg_db_host: str = "localhost"
    pg_db_port: int = 5432
    soundfont_path: str = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
    debug: bool = False
    logging_level: str = "INFO"
    allowed_origins: str = "https://melodygenerator.fun"

    @property
    def cors_origins(self) -> list[str]:
        """Parse allowed origins from comma-separated string, adding localhost in debug mode."""
        origins = [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
        if self.debug and "http://localhost:3000" not in origins:
            origins.append("http://localhost:3000")
        return origins
