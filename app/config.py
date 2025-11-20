import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database configuration
    postgres_user: str = Field(default="openwebui", env="POSTGRES_USER")
    postgres_password: str = Field(default="", env="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="openwebui", env="POSTGRES_DB")
    postgres_host: str = Field(default="postgres", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    
    @property
    def database_url(self) -> str:
        """Construct database URL from components."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    # OpenRouter API settings
    openrouter_api_key: str = Field(default="", env="OPENROUTER_API_KEY")
    openai_api_base_url: str = Field(default="https://openrouter.ai/api/v1", env="OPENAI_API_BASE_URL")
    openai_model: Optional[str] = "google/gemini-2.5-flash"  # 1M context, stable release
    
    # Open WebUI configuration
    webui_secret_key: Optional[str] = None
    
    # Async database URL (for API)
    @property
    def async_database_url(self) -> str:
        """Convert database URL to async format for asyncpg."""
        db_url = self.database_url  # Call the property
        if db_url.startswith("postgresql://"):
            return db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return db_url
    
    # SSL/TLS configuration for mTLS (optional)
    ssl_ca_cert: Optional[str] = None
    ssl_server_cert: Optional[str] = None
    ssl_server_key: Optional[str] = None
    
    # Application settings
    app_host: str = "0.0.0.0"
    app_port: int = 8443
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
