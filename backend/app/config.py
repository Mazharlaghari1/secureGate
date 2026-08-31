import json
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "securegate-production-secret-key-9a2b8e3d6f1c4e7a8b0c9d8e7f6a5b4c"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "event_access"
    ALLOWED_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5000"
    ]
    MAX_CSV_FILE_SIZE_MB: int = 2
    FRONTEND_URL: str = "http://localhost:5173"
    QR_TOKEN_TTL_SECONDS: int = 60
    INITIAL_ADMIN_EMAIL: str = "admin@securegate.com"
    INITIAL_ADMIN_PASSWORD: str = "Admin12345!"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v_clean = v.strip()
            if v_clean.startswith("[") and v_clean.endswith("]"):
                try:
                    return json.loads(v_clean)
                except Exception:
                    pass
            return [i.strip() for i in v_clean.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
