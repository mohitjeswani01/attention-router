from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/attention_router"
    ao_daemon_base_url: str = "http://127.0.0.1:3001"
    ao_daemon_timeout: float = 30.0
    log_level: str = "INFO"


settings = Settings()