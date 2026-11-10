from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://interviewiq:interviewiq@db:5432/interviewiq"
    redis_url: str = "redis://redis:6379/0"
    secret_key: str = "change-me"
    access_token_minutes: int = 60 * 24

    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-5-5"

    cors_origins: str = "http://localhost:5173"
    max_questions: int = 8
    code_timeout_seconds: int = 5
    celery_eager: bool = False


settings = Settings()
