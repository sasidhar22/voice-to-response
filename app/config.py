from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"

    bedrock_llm_model_id: str = "us.anthropic.claude-sonnet-4-5"

    transcribe_language_code: str = "en-US"
    transcribe_sample_rate: int = 16000

    database_url: str = "postgresql+asyncpg://grocery:grocery@localhost:5432/grocery"


settings = Settings()
