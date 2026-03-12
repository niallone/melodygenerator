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

    # R2 storage (S3-compatible)
    r2_endpoint_url: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = ""
    r2_public_url: str = ""

    @property
    def r2_enabled(self) -> bool:
        return bool(self.r2_endpoint_url and self.r2_access_key_id and self.r2_bucket_name)

    @property
    def cors_origins(self) -> list[str]:
        """Parse allowed origins from comma-separated string, adding localhost in debug mode."""
        origins = [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
        if self.debug and "http://localhost:3000" not in origins:
            origins.append("http://localhost:3000")
        return origins
