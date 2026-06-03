"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4.1-mini"
    openai_whisper_model: str = "whisper-1"
    openai_realtime_model: str = "gpt-realtime"
    openai_tts_voice: str = "verse"

    supabase_url: str = ""
    supabase_service_role_key: str = ""
    database_url: str = ""

    cors_origins: str = "http://localhost:3000"

    chunk_size_tokens: int = 600
    chunk_overlap_tokens: int = 80
    retrieval_top_k: int = 12

    max_upload_files: int = 20
    max_file_size_mb: int = 2
    max_audio_size_mb: int = 25

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
