from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM provider: "bedrock" (production) or "ollama" (local dev)
    llm_provider: str = "bedrock"

    # Ollama — used when llm_provider=ollama
    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434"

    # AWS Bedrock — used when llm_provider=bedrock
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    bedrock_llm_model_id: str = "us.anthropic.claude-sonnet-4-5"

    # AWS Transcribe
    transcribe_language_code: str = "en-US"
    transcribe_sample_rate: int = 16000

    # Database — SQLite for local dev, PostgreSQL for production
    database_url: str = "sqlite+aiosqlite:///./grocery.db"


settings = Settings()
