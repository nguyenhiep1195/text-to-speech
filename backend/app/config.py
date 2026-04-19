from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    TTS_USERNAME: str = "admin"
    TTS_PASSWORD: str = "admin123"
    SECRET_KEY: str = "supersecretkey-change-in-production-32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    CORS_ORIGINS: str = "http://localhost:3000"

    model_config = {"env_file": Path(__file__).parent.parent / ".env", "extra": "ignore"}

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]


settings = Settings()
