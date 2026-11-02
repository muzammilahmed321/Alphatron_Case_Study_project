from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py is at campuspilot/backend/app/core/, so the root is 4 levels up
ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    database_url: str = ""
    secret_key: str = "dev-secret"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""                 
    gemini_model: str = "gemini-3.5-flash"   

    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")


settings = Settings()