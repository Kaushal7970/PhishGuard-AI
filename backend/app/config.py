from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    secret_key: str = "development-only-change-me"
    database_url: str = "sqlite:///./phishguard.db"
    cors_origins: str = "http://localhost:5173"
    model_dir: Path = Path(__file__).resolve().parents[1] / "model"
    access_token_minutes: int = 60

    model_config = SettingsConfigDict(env_prefix="PHISHGUARD_", env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
