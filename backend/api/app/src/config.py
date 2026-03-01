from pydantic import ConfigDict, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(env_file=".env", extra="ignore")

    secret_key: str = "change-me-in-production"
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

    @model_validator(mode="after")
    def validate_secret_key(self):
        if self.secret_key == "change-me-in-production":
            if not self.debug:
                raise ValueError("secret_key must be changed from default in production")
        if len(self.secret_key) < 20:
            if not self.debug:
                raise ValueError("secret_key must be at least 20 characters long")
        return self
