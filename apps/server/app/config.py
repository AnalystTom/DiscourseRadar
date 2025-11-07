"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_env: str = "local"

    # API Keys
    gemini_api_key: str
    firecrawl_api_key: str

    # Database
    postgres_url: str

    # Source Control
    allowed_sources: str = "reddit.com,news.ycombinator.com"
    reddit_compliance_mode: str = "strict_api"

    # Crawl Configuration
    max_crawl_depth: int = 3
    crawl_concurrency: int = 5
    crawl_interval_seconds: int = 2

    # Analysis Configuration
    emerging_topic_threshold: float = 0.75

    # GCP Configuration
    gcloud_project: str = ""
    region: str = "us-central1"

    # Service URLs
    client_url: str = "http://localhost:5173"
    server_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
