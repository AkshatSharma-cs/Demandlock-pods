import os

from pydantic import BaseModel


class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./demandlock.db")
    audio_dir: str = os.getenv("AUDIO_DIR", "./media/audio")
    pod_threshold: int = int(os.getenv("POD_THRESHOLD", "5"))
    enable_asr: bool = os.getenv("ENABLE_ASR", "false").lower() in {"1", "true", "yes", "on"}
    demo_mode: bool = os.getenv("DEMO_MODE", "true").lower() in {"1", "true", "yes", "on"}
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
