"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "sqlite:///./dns_snapshots.db"

    # API Configuration
    API_KEY: str = "change-me-in-production"
    API_V1_PREFIX: str = "/api/v1"

    # Infoblox Configuration
    INFOBLOX_URL: str = ""
    INFOBLOX_USERNAME: str = ""
    INFOBLOX_PASSWORD: str = ""
    INFOBLOX_WAPI_VERSION: str = "v2.12"
    INFOBLOX_VERIFY_SSL: bool = True

    # Application Settings
    EXPORT_DIR: str = "./exports"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


settings = Settings()
