from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"  # always backend/.env


class Settings(BaseSettings):
    """
    Central place for all configuration. Values are read from environment
    variables / a local .env file — never hardcode secrets here.
    """

    database_url: str = "postgresql://postgres:postgres@localhost:5432/mit_mobile_billing"
    openai_api_key: str | None = None
    frontend_origin: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")


settings = Settings()