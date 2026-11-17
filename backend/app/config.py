from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+psycopg://ecospot:ecospot@127.0.0.1:5433/ecospot"
    jwt_secret: str = "ecospot-dev-secret-change-me-in-production-2026"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24
    upload_dir: Path = BASE_DIR / "uploads"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
