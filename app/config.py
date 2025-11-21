from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database configuration
    postgres_user: str = Field(default="openwebui", validation_alias="POSTGRES_USER")
    postgres_password: str = Field(default="", validation_alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="openwebui", validation_alias="POSTGRES_DB")
    postgres_host: str = Field(default="postgres", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, validation_alias="POSTGRES_PORT")

    @property
    def database_url(self) -> str:
        """Construct database URL from components."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # OpenRouter API settings
    openrouter_api_key: str = Field(default="", validation_alias="OPENROUTER_API_KEY")
    openai_api_base_url: str = Field(
        default="https://openrouter.ai/api/v1", validation_alias="OPENAI_API_BASE_URL"
    )
    openai_model: str | None = "google/gemini-2.5-flash"  # 1M context, stable release

    # Open WebUI configuration
    webui_secret_key: str | None = None

    # Async database URL (for API)
    @property
    def async_database_url(self) -> str:
        """Convert database URL to async format for asyncpg."""
        db_url = self.database_url  # Call the property
        if db_url.startswith("postgresql://"):
            return db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return db_url

    # SSL/TLS configuration for mTLS (optional)
    ssl_ca_cert: str | None = None
    ssl_server_cert: str | None = None
    ssl_server_key: str | None = None

    # Observability
    otlp_endpoint: str | None = Field(default=None, validation_alias="OTLP_ENDPOINT")

    # Application settings
    app_host: str = "0.0.0.0"  # nosec B104
    app_port: int = 8443

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()
